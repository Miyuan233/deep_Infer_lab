"""模型文件校验器的 CPU 侧单元测试。"""

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.verify_model_snapshot import verify_file, verify_snapshot


class VerifySnapshotTests(unittest.TestCase):
    def test_正常文件(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b"abc"
            (root / "sample.bin").write_bytes(payload)
            entry = {"path": "sample.bin", "size": 3, "sha256": hashlib.sha256(payload).hexdigest()}
            result = verify_snapshot(root, {"files": [entry], "revision": "test"})
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["verified_bytes"], 3)

    def test_大小不符(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.bin").write_bytes(b"abc")
            result = verify_file(root, {"path": "sample.bin", "size": 4, "sha256": "0" * 64})
            self.assertEqual(result["status"], "size_mismatch")

    def test_哈希不符(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.bin").write_bytes(b"abc")
            result = verify_file(root, {"path": "sample.bin", "size": 3, "sha256": "0" * 64})
            self.assertEqual(result["status"], "hash_mismatch")

    def test_拒绝路径穿越(self) -> None:
        with self.assertRaises(ValueError):
            verify_file(Path("."), {"path": "../secret", "size": 0, "sha256": "0" * 64})

    def test_拒绝重复路径(self) -> None:
        entry = {"path": "same", "size": 0, "sha256": "0" * 64}
        with self.assertRaises(ValueError):
            verify_snapshot(Path("."), {"files": [entry, entry]})

    def test_拒绝清单总数不一致(self) -> None:
        entry = {"path": "same", "size": 1, "sha256": "0" * 64}
        with self.assertRaises(ValueError):
            verify_snapshot(Path("."), {"files": [entry], "total_bytes": 2})


if __name__ == "__main__":
    unittest.main()
