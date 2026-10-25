"""M1 工作负载生成器的纯 CPU 单元测试。"""

import unittest
from collections import UserDict

from scripts.prepare_m1_workload import chat_token_ids, nearest_repetitions, request_text


class FakeTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        self.last_arguments = (tokenize, add_generation_prompt)
        return {"input_ids": [1] * len(messages[0]["content"].split()), "attention_mask": [1]}


class MappingTokenizer(FakeTokenizer):
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        return UserDict(super().apply_chat_template(messages, tokenize, add_generation_prompt))


class WorkloadPreparationTests(unittest.TestCase):
    def test_从_input_ids_获取长度(self) -> None:
        tokenizer = FakeTokenizer()
        tokens = chat_token_ids(tokenizer, [{"role": "user", "content": "一 二 三"}])
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokenizer.last_arguments, (True, True))

    def test_支持非_dict_映射返回值(self) -> None:
        tokens = chat_token_ids(MappingTokenizer(), [{"role": "user", "content": "一 二 三 四"}])
        self.assertEqual(len(tokens), 4)

    def test_寻找最接近的长度(self) -> None:
        repetitions, actual = nearest_repetitions(128, lambda number: 12 + 9 * number)
        self.assertEqual((repetitions, actual), (13, 129))

    def test_拒绝非法目标(self) -> None:
        with self.assertRaises(ValueError):
            nearest_repetitions(0, lambda number: number)

    def test_请求编号先于重复背景(self) -> None:
        text = request_text(20261024, 0, 2, 3, 128)
        self.assertTrue(text.startswith("实验编号 20261024-0-2"))
        self.assertIn("请分四点", text)


if __name__ == "__main__":
    unittest.main()
