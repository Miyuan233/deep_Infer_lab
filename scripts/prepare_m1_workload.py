"""使用本地 Tokenizer 离线准备 M1 的确定性聊天请求。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


BACKGROUND = (
    "GPU 推理包含请求调度、预填充、KV 缓存和逐 Token 解码。"
    "混合专家模型只激活部分专家，端到端延迟还受到数据移动与批处理影响。"
)
INSTRUCTIONS = {
    128: "请分四点说明这段背景中的主要概念，每点给出简短解释。",
    512: "请按十二个编号小节详细解释这段背景，并分析延迟、吞吐量和显存之间的权衡。",
}


def chat_token_ids(tokenizer: Any, messages: list[dict[str, str]]) -> list[int]:
    """只统计实际聊天模板编码中的 input_ids，不把字段数当作 Token 数。"""

    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    token_ids = encoded["input_ids"] if isinstance(encoded, Mapping) else encoded
    if not isinstance(token_ids, list) or not all(isinstance(token, int) for token in token_ids):
        raise TypeError("Tokenizer 未返回单请求的一维 input_ids")
    return token_ids


def request_text(seed: int, group_index: int, sample_index: int, repetitions: int, output_target: int) -> str:
    """把唯一编号放在开头，减小不同请求的共享前缀。"""

    instruction = INSTRUCTIONS.get(output_target)
    if instruction is None:
        raise ValueError(f"未定义输出目标 {output_target} 的请求指令")
    return (
        f"实验编号 {seed}-{group_index}-{sample_index}。以下是技术背景："
        + BACKGROUND * repetitions
        + instruction
    )


def nearest_repetitions(
    target_tokens: int, count_for_repetitions: Callable[[int], int], max_repetitions: int = 4096
) -> tuple[int, int]:
    """二分查找接近目标长度的重复次数，并返回真实 Token 数。"""

    if target_tokens < 1:
        raise ValueError("目标输入 Token 数必须为正")
    cached: dict[int, int] = {}

    def count(repetitions: int) -> int:
        if repetitions not in cached:
            cached[repetitions] = count_for_repetitions(repetitions)
        return cached[repetitions]

    low, high = 0, 1
    while high < max_repetitions and count(high) < target_tokens:
        low, high = high, min(high * 2, max_repetitions)
    if count(high) < target_tokens:
        raise ValueError("达到最大重复次数后仍无法满足目标长度")
    while low + 1 < high:
        middle = (low + high) // 2
        if count(middle) < target_tokens:
            low = middle
        else:
            high = middle
    candidates = {0, low, high}
    candidates.update(range(max(0, high - 2), min(max_repetitions, high + 2) + 1))
    best = min(candidates, key=lambda repetitions: (abs(count(repetitions) - target_tokens), repetitions))
    return best, count(best)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def prepare(plan_path: Path, model_path: Path, output_dir: Path, samples_per_group: int) -> dict[str, Any]:
    """生成请求 JSONL 和清单；不访问网络，也不初始化 GPU。"""

    if samples_per_group < 1:
        raise ValueError("每组请求数量必须为正")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != 1 or not isinstance(plan.get("groups"), list):
        raise ValueError("工作负载配置格式不受支持")
    if not model_path.is_dir() or not (model_path / "tokenizer.json").is_file():
        raise FileNotFoundError("本地模型目录缺少 tokenizer.json")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    requests: list[dict[str, Any]] = []
    maximum_length = int(plan["max_model_len_proposal"])
    for group_index, group in enumerate(plan["groups"]):
        target_input = int(group["target_input_tokens"])
        target_output = int(group["target_output_tokens"])
        if target_input < 1 or target_output < 1 or not group.get("concurrencies"):
            raise ValueError("工作负载分组包含非法 Token 数或空并发列表")
        for sample_index in range(samples_per_group):
            def count_for(repetitions: int) -> int:
                text = request_text(plan["seed"], group_index, sample_index, repetitions, target_output)
                return len(chat_token_ids(tokenizer, [{"role": "user", "content": text}]))

            repetitions, actual_input = nearest_repetitions(target_input, count_for)
            tolerance = max(8, round(target_input * 0.03))
            if abs(actual_input - target_input) > tolerance:
                raise ValueError(f"分组 {group['name']} 的输入长度偏差超过容限：{actual_input}")
            if actual_input + target_output > maximum_length:
                raise ValueError("输入 Token 数与输出上限之和超过计划的最大上下文")
            text = request_text(plan["seed"], group_index, sample_index, repetitions, target_output)
            requests.append({
                "request_id": f"g{group_index:02d}-s{sample_index:02d}",
                "group": group["name"],
                "sample_index": sample_index,
                "messages": [{"role": "user", "content": text}],
                "target_input_tokens": target_input,
                "input_tokens": actual_input,
                "target_output_tokens": target_output,
                "max_tokens": target_output,
                "repetitions": repetitions,
            })

    output_dir.mkdir(parents=True, exist_ok=False)
    request_path = output_dir / "requests.jsonl"
    with request_path.open("w", encoding="utf-8", newline="\n") as destination:
        for request in requests:
            destination.write(json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n")
    summary = {
        "schema_version": 1,
        "status": "prepared_cpu_only_not_benchmarked",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(Path(__file__).resolve().parents[1]),
        "plan_path": str(plan_path.resolve()),
        "plan_sha256": _sha256(plan_path),
        "model_path": str(model_path.resolve()),
        "model_revision": plan["model_revision"],
        "tokenizer_json_sha256": _sha256(model_path / "tokenizer.json"),
        "tokenizer_class": type(tokenizer).__name__,
        "seed": plan["seed"],
        "samples_per_group": samples_per_group,
        "request_count": len(requests),
        "requests_sha256": _sha256(request_path),
        "groups": [
            {
                "name": group["name"],
                "concurrencies_planned": group["concurrencies"],
                "target_input_tokens": group["target_input_tokens"],
                "actual_input_tokens": [
                    request["input_tokens"] for request in requests if request["group"] == group["name"]
                ],
                "target_output_tokens": group["target_output_tokens"],
            }
            for group in plan["groups"]
        ],
        "note": "输出 Token 数是未来请求上限，不是本次测得的模型输出。",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("configs/m1-workload-plan.json"))
    parser.add_argument("--model", type=Path, default=Path("models/DeepSeek-V2-Lite-Chat"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples-per-group", type=int, default=8)
    arguments = parser.parse_args()
    summary = prepare(arguments.plan, arguments.model, arguments.output_dir, arguments.samples_per_group)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
