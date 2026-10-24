"""依据固定修订的文件清单独立校验模型快照；不加载模型或初始化 GPU。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def verify_file(root: Path, entry: dict[str, object]) -> dict[str, object]:
    """按大小与 SHA-256 校验单个相对路径，拒绝目录穿越。"""

    name = entry["path"]
    expected_size = entry["size"]
    expected_hash = entry["sha256"]
    if not isinstance(name, str) or not isinstance(expected_size, int) or not isinstance(expected_hash, str):
        raise ValueError("清单字段类型不正确")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"非法相对路径：{name}")
    target = root / relative
    if not target.is_file() or target.is_symlink():
        return {"path": name, "status": "missing_or_symlink"}
    actual_size = target.stat().st_size
    if actual_size != expected_size:
        return {"path": name, "status": "size_mismatch", "expected": expected_size, "actual": actual_size}

    digest = hashlib.sha256()
    with target.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    actual_hash = digest.hexdigest()
    if actual_hash != expected_hash:
        return {"path": name, "status": "hash_mismatch", "expected": expected_hash, "actual": actual_hash}
    return {"path": name, "status": "passed", "size": actual_size, "sha256": actual_hash}


def verify_snapshot(root: Path, manifest: dict[str, object]) -> dict[str, object]:
    """校验清单列出的全部文件，并汇总结果。"""

    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("清单中没有文件")
    paths = [entry.get("path") for entry in entries if isinstance(entry, dict)]
    if len(paths) != len(entries) or len(paths) != len(set(paths)):
        raise ValueError("文件清单有非法项或重复路径")
    expected_total = manifest.get("total_bytes")
    if expected_total is not None:
        if not isinstance(expected_total, int) or sum(entry["size"] for entry in entries) != expected_total:
            raise ValueError("清单总字节数与文件明细不一致")
    results = [verify_file(root, entry) for entry in entries]
    status = "passed" if all(result["status"] == "passed" for result in results) else "failed"
    return {
        "status": status,
        "source": manifest.get("source"),
        "revision": manifest.get("revision"),
        "file_count": len(entries),
        "verified_bytes": sum(result.get("size", 0) for result in results),
        "files": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验模型快照的大小和 SHA-256；不使用 GPU")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    with args.manifest.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    result = verify_snapshot(args.model_dir, manifest)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
