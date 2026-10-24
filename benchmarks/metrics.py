"""M1 服务基准的客户端指标计算；此模块不连接服务，也不初始化 GPU。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class RequestTiming:
    """单请求原始时间点，使用同一个单调时钟的纳秒值。"""

    sent_ns: int
    first_output_ns: int
    finished_ns: int
    output_event_ns: tuple[int, ...]
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class RequestMetrics:
    """可直接序列化保存的单请求派生指标。"""

    input_tokens: int
    output_tokens: int
    latency_ms: float
    ttft_ms: float
    tpot_ms: float | None
    itl_ms: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        """转为 JSON 可保存的普通字典。"""

        return asdict(self)


def calculate_request_metrics(timing: RequestTiming) -> RequestMetrics:
    """按照客户端流式输出时间点计算 TTFT、TPOT 与 ITL。"""

    if timing.sent_ns < 0:
        raise ValueError("发送时间不能为负数")
    if timing.input_tokens < 0 or timing.output_tokens < 1:
        raise ValueError("输入 Token 数不能为负，输出 Token 数至少为 1")
    if not timing.output_event_ns:
        raise ValueError("至少需要一个非空流式输出事件")
    if timing.output_event_ns[0] != timing.first_output_ns:
        raise ValueError("首个输出时间必须等于首个输出事件时间")
    if not timing.sent_ns <= timing.first_output_ns <= timing.finished_ns:
        raise ValueError("发送、首输出、完成时间必须有序")
    if any(
        earlier > later
        for earlier, later in zip(timing.output_event_ns, timing.output_event_ns[1:])
    ) or timing.output_event_ns[-1] > timing.finished_ns:
        raise ValueError("输出事件时间必须有序且不晚于完成时间")

    ns_to_ms = 1e-6
    latency_ms = (timing.finished_ns - timing.sent_ns) * ns_to_ms
    ttft_ms = (timing.first_output_ns - timing.sent_ns) * ns_to_ms
    tpot_ms = (
        (timing.finished_ns - timing.first_output_ns) * ns_to_ms / (timing.output_tokens - 1)
        if timing.output_tokens > 1
        else None
    )
    itl_ms = tuple(
        (later - earlier) * ns_to_ms
        for earlier, later in zip(timing.output_event_ns, timing.output_event_ns[1:])
    )
    return RequestMetrics(
        input_tokens=timing.input_tokens,
        output_tokens=timing.output_tokens,
        latency_ms=latency_ms,
        ttft_ms=ttft_ms,
        tpot_ms=tpot_ms,
        itl_ms=itl_ms,
    )


def percentile(values: Iterable[float], percentage: float) -> float:
    """按线性插值计算分位数；空样本必须由调用方显式处理。"""

    ordered = sorted(values)
    if not ordered:
        raise ValueError("不能对空样本计算分位数")
    if not 0 <= percentage <= 100 or not isfinite(percentage):
        raise ValueError("分位数必须是 0 到 100 之间的有限数")
    if any(not isfinite(value) for value in ordered):
        raise ValueError("样本必须都是有限数")
    position = (len(ordered) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
