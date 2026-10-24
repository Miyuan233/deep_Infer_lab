#!/usr/bin/env python3
"""在显式授权的 GPU 上执行短时 PyTorch 与 Triton 正确性检查。"""

import argparse
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def csv_rows(raw: str) -> list[list[str]]:
    return [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(raw)) if row]


def validate_gpu(
    index: int,
    gpu_table: str,
    app_table: str,
    existing_visible: str | None,
) -> dict[str, str | int]:
    """只解析设备状态；任何不确定或已占用状态都拒绝运行。"""
    matches = []
    for row in csv_rows(gpu_table):
        if len(row) != 4:
            raise RuntimeError("无法解析 nvidia-smi 设备清单")
        try:
            row_index = int(row[0])
            total_mib = int(row[2])
            used_mib = int(row[3])
        except ValueError as exc:
            raise RuntimeError("nvidia-smi 设备清单包含非数字字段") from exc
        if row_index == index:
            matches.append({"index": row_index, "uuid": row[1], "total_mib": total_mib, "used_mib": used_mib})

    if len(matches) != 1:
        raise RuntimeError(f"GPU {index} 不存在或设备清单不唯一")
    selected = matches[0]
    uuid = str(selected["uuid"])
    if not uuid.startswith("GPU-"):
        raise RuntimeError("GPU UUID 格式异常")
    if existing_visible not in (None, "", str(index), uuid):
        raise RuntimeError("CUDA_VISIBLE_DEVICES 与指定 GPU 不一致")

    for row in csv_rows(app_table):
        if len(row) < 2:
            raise RuntimeError("无法解析 nvidia-smi 计算进程清单")
        if row[0] == uuid:
            raise RuntimeError(f"GPU {index} 已有计算进程，拒绝运行")

    if int(selected["used_mib"]) > 256:
        raise RuntimeError(f"GPU {index} 已占用显存超过 256 MiB，拒绝运行")
    if int(selected["total_mib"]) - int(selected["used_mib"]) < 4096:
        raise RuntimeError(f"GPU {index} 可用显存不足 4 GiB，拒绝运行")
    return selected


def nvidia_smi(*args: str) -> str:
    completed = subprocess.run(
        ["nvidia-smi", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout


def run_checks(selected: dict[str, str | int]) -> dict[str, object]:
    """在设备 UUID 已固定后才导入会使用 CUDA 的框架。"""
    os.environ["CUDA_VISIBLE_DEVICES"] = str(selected["uuid"])

    import torch
    import triton

    from _triton_smoke_kernel import add_kernel

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("PyTorch 未看到且仅看到指定的一张 CUDA GPU")

    properties = torch.cuda.get_device_properties(0)
    if (properties.major, properties.minor) != (9, 0):
        raise RuntimeError(f"设备计算能力为 {properties.major}.{properties.minor}，不是预期的 H200 sm_90")

    n_elements = 1024
    x = torch.arange(n_elements, device="cuda", dtype=torch.float32)
    y = torch.full((n_elements,), 2.0, device="cuda", dtype=torch.float32)
    reference = x + y
    output = torch.empty_like(x)
    add_kernel[(triton.cdiv(n_elements, 256),)](x, y, output, n_elements, BLOCK_SIZE=256)
    torch.cuda.synchronize()
    correct = bool(torch.allclose(output, reference, rtol=0, atol=0))
    if not correct:
        raise RuntimeError("Triton 输出与 PyTorch 参考结果不一致")

    result = {
        "torch_version": torch.__version__,
        "torch_cuda_build": torch.version.cuda,
        "triton_version": triton.__version__,
        "device_name": properties.name,
        "compute_capability": f"{properties.major}.{properties.minor}",
        "elements": n_elements,
        "torch_and_triton_correct": correct,
        "peak_allocated_mib": round(torch.cuda.max_memory_allocated() / (1024**2), 2),
        "peak_reserved_mib": round(torch.cuda.max_memory_reserved() / (1024**2), 2),
    }
    del x, y, reference, output
    torch.cuda.empty_cache()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu-index", type=int, required=True, help="用户明确授权的 nvidia-smi GPU 编号")
    args = parser.parse_args()
    if args.gpu_index < 0:
        parser.error("GPU 编号不能为负数")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = PROJECT_ROOT / "results" / "m0" / f"{timestamp}-gpu-smoke-gpu{args.gpu_index}"
    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record: dict[str, object] = {
        "timestamp_utc": timestamp,
        "requested_gpu_index": args.gpu_index,
        "purpose": "PyTorch 与 Triton 正确性及工具链 Smoke Test；不用于性能比较",
    }

    try:
        revision = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        record["git_commit"] = revision.stdout.strip()
        gpu_table = nvidia_smi(
            "--query-gpu=index,uuid,memory.total,memory.used",
            "--format=csv,noheader,nounits",
        )
        app_table = nvidia_smi(
            "--query-compute-apps=gpu_uuid,pid",
            "--format=csv,noheader,nounits",
        )
        selected = validate_gpu(args.gpu_index, gpu_table, app_table, os.environ.get("CUDA_VISIBLE_DEVICES"))
        record["preflight"] = selected
        record["checks"] = run_checks(selected)
        record["status"] = "passed"
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
        output_path = output_dir / "result.json"
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output_path)
        print(f"状态：{record['status']}")
        if record["status"] == "failed":
            print(record.get("error", "未知错误"), file=sys.stderr)
    return 0 if record["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
