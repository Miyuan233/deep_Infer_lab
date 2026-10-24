"""M1 客户端指标的 CPU 侧单元测试。"""

import unittest

from benchmarks.metrics import RequestTiming, calculate_request_metrics, percentile


class RequestMetricsTests(unittest.TestCase):
    def test_正常请求的指标(self) -> None:
        timing = RequestTiming(
            sent_ns=0,
            first_output_ns=100_000_000,
            finished_ns=400_000_000,
            output_event_ns=(100_000_000, 200_000_000, 300_000_000),
            input_tokens=128,
            output_tokens=4,
        )
        metrics = calculate_request_metrics(timing)
        self.assertEqual(metrics.latency_ms, 400)
        self.assertEqual(metrics.ttft_ms, 100)
        self.assertEqual(metrics.tpot_ms, 100)
        self.assertEqual(metrics.itl_ms, (100, 100))
        self.assertEqual(metrics.to_dict()["output_tokens"], 4)

    def test_单个输出_token_没有_tpot(self) -> None:
        timing = RequestTiming(0, 10_000_000, 20_000_000, (10_000_000,), 1, 1)
        metrics = calculate_request_metrics(timing)
        self.assertIsNone(metrics.tpot_ms)
        self.assertEqual(metrics.itl_ms, ())

    def test_多个_token_同一事件不伪造_itl(self) -> None:
        timing = RequestTiming(0, 40_000_000, 180_000_000, (40_000_000, 80_000_000), 1, 4)
        metrics = calculate_request_metrics(timing)
        self.assertAlmostEqual(metrics.tpot_ms, 140 / 3)
        self.assertEqual(metrics.itl_ms, (40,))

    def test_时间乱序被拒绝(self) -> None:
        timing = RequestTiming(0, 20, 30, (20, 10), 1, 2)
        with self.assertRaises(ValueError):
            calculate_request_metrics(timing)

    def test_首个事件必须是实际输出(self) -> None:
        timing = RequestTiming(0, 10, 30, (20,), 1, 1)
        with self.assertRaises(ValueError):
            calculate_request_metrics(timing)


class PercentileTests(unittest.TestCase):
    def test_线性插值(self) -> None:
        self.assertEqual(percentile([4, 1, 2, 3], 50), 2.5)
        self.assertEqual(percentile([1, 2, 3, 4, 5], 90), 4.6)

    def test_非法输入(self) -> None:
        for values, percentage in (([], 50), ([1], -1), ([1], 101), ([float("nan")], 50)):
            with self.subTest(values=values, percentage=percentage):
                with self.assertRaises(ValueError):
                    percentile(values, percentage)


if __name__ == "__main__":
    unittest.main()
