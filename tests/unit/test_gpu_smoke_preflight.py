"""GPU Smoke Test 的 CPU 侧资源保护测试。"""

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from gpu_smoke import validate_gpu


GPU_TABLE = "3, GPU-example-uuid, 143771, 0\n"


class PreflightTests(unittest.TestCase):
    def test_idle_authorized_index_passes(self):
        selected = validate_gpu(3, GPU_TABLE, "", None)
        self.assertEqual(selected["uuid"], "GPU-example-uuid")

    def test_existing_process_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "已有计算进程"):
            validate_gpu(3, GPU_TABLE, "GPU-example-uuid, 123\n", None)

    def test_used_memory_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "已占用显存"):
            validate_gpu(3, "3, GPU-example-uuid, 143771, 257\n", "", None)

    def test_other_visible_device_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "CUDA_VISIBLE_DEVICES"):
            validate_gpu(3, GPU_TABLE, "", "2")

    def test_unknown_index_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "不存在"):
            validate_gpu(1, GPU_TABLE, "", None)


if __name__ == "__main__":
    unittest.main()
