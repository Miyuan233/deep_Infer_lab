"""在指定的空闲 H200 上进行一次离线模型功能验证。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path


def _command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def _check_gpu(index: int, expected_uuid: str) -> dict[str, object]:
    rows = _command(
        "nvidia-smi",
        "--query-gpu=index,uuid,name,memory.total,memory.used,memory.free",
        "--format=csv,noheader,nounits",
    ).splitlines()
    devices = [[part.strip() for part in row.split(",")] for row in rows]
    matches = [device for device in devices if int(device[0]) == index]
    if len(matches) != 1:
        raise RuntimeError(f"未找到唯一的 GPU {index}")
    device = matches[0]
    if device[1] != expected_uuid:
        raise RuntimeError(f"GPU {index} 的 UUID 与授权设备不一致：{device[1]}")
    if int(device[4]) != 0:
        raise RuntimeError(f"GPU {index} 已占用 {device[4]} MiB，取消本次验证")
    processes = _command(
        "nvidia-smi",
        "--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory",
        "--format=csv,noheader",
    )
    if any(row.split(",", 1)[0].strip() == expected_uuid for row in processes.splitlines()):
        raise RuntimeError(f"GPU {index} 出现计算进程，取消本次验证")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != expected_uuid:
        raise RuntimeError("CUDA_VISIBLE_DEVICES 未限定为授权 GPU 的 UUID")
    return {
        "index": index,
        "uuid": device[1],
        "name": device[2],
        "total_mib": int(device[3]),
        "used_mib_before": int(device[4]),
        "free_mib_before": int(device[5]),
        "compute_processes_before": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu-index", type=int, required=True)
    parser.add_argument("--gpu-uuid", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    args = parser.parse_args()

    result_dir = args.result_dir.resolve()
    result_dir.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    record: dict[str, object] = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "短时离线功能验证；非性能 Benchmark",
        "git_commit": _command("git", "-C", str(Path(__file__).resolve().parents[1]), "rev-parse", "HEAD"),
        "model_path": str(args.model.resolve()),
        "model_revision": "d174ca84ff4d8cd51f8e927bcb1242555e31b2c0",
        "gpu_index_authorized": args.gpu_index,
        "gpu_uuid_authorized": args.gpu_uuid,
        "engine": {
            "tensor_parallel_size": 1,
            "dtype": "bfloat16",
            "gpu_memory_utilization": 0.45,
            "max_model_len": 4096,
            "max_num_seqs": 4,
            "enforce_eager": True,
        },
        "generation": {"temperature": 0, "max_tokens": 32},
        "status": "started",
    }
    result_file = result_dir / "result.json"

    def save() -> None:
        record["elapsed_seconds"] = round(time.monotonic() - start, 3)
        result_file.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
            raise RuntimeError("必须设置 HF_HUB_OFFLINE=1 和 TRANSFORMERS_OFFLINE=1")
        if not args.model.is_dir():
            raise FileNotFoundError(args.model)
        record["gpu_preflight"] = _check_gpu(args.gpu_index, args.gpu_uuid)
        save()

        import torch
        from vllm import LLM, SamplingParams

        if torch.cuda.device_count() != 1:
            raise RuntimeError(f"PyTorch 可见 GPU 数量不是 1：{torch.cuda.device_count()}")
        record["torch_visible_gpu_count"] = torch.cuda.device_count()
        record["torch_visible_gpu_name"] = torch.cuda.get_device_name(0)
        record["torch_version"] = torch.__version__
        save()

        engine = LLM(model=str(args.model.resolve()), **record["engine"])
        record["status"] = "model_loaded"
        save()
        prompt = "请用一句话解释什么是 GPU 推理。"
        outputs = engine.generate([prompt], SamplingParams(**record["generation"]))
        if len(outputs) != 1 or len(outputs[0].outputs) != 1:
            raise RuntimeError("生成结果数量不符合预期")
        generated = outputs[0].outputs[0]
        record["prompt"] = prompt
        record["output_text"] = generated.text
        record["output_token_count"] = len(generated.token_ids)
        record["finish_reason"] = generated.finish_reason
        record["status"] = "passed" if generated.token_ids else "failed_empty_output"
        save()
        return 0 if generated.token_ids else 1
    except BaseException as error:
        record["status"] = "failed"
        record["error_type"] = type(error).__name__
        record["error_message"] = str(error)
        record["traceback"] = traceback.format_exc()
        save()
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
