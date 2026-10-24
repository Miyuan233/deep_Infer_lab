# M1 单卡推理基线：候选与实验设计

## 先学会区分两个阶段

第一阶段用较小的 dense 模型验证完整测量链：权重版本固定、服务配置固定、请求可重复、原始数据可追溯。第二阶段根据真实瓶颈选择较大 dense 模型或 MoE 模型。第一阶段的结果不能代替第二阶段的性能结论。

## 候选模型（尚未下载）

| 候选 | 上游参数量 | BF16 权重理论下限 | 研究用途 |
| --- | ---: | ---: | --- |
| [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | 8.2B | 约 15.3 GiB | 优先用于单卡服务与测量链路联调 |
| [Qwen3-32B](https://huggingface.co/Qwen/Qwen3-32B) | 32.8B | 约 61.1 GiB | 后续研究更大 dense 模型的 Prefill/Decode 瓶颈 |
| [Qwen3-30B-A3B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507) | 30.5B 总参数、3.3B 激活参数 | 约 56.8 GiB | 后续研究专家路由与 MoE 推理路径 |

上述 GiB 数值只用“参数量 × 2 字节 ÷ 2³⁰”估算 BF16 权重，不是模型仓库的精确下载量，也不是 vLLM 实际显存占用。后者还包括 KV Cache、工作区、CUDA 上下文、编译缓存与框架开销。下载前须核对所选修订版本的文件清单与实际字节数；启动前须设置显存余量并重新检查授权 GPU。

2026-10-24 在[Qwen3-8B 官方文件页](https://huggingface.co/Qwen/Qwen3-8B/tree/main)看到当前修订为 `b968826d9c46dd6066d109eabc6255188de91218`，仓库显示总大小约 16.4 GB，包含 5 个 Safetensors 权重分片。服务器 `/home` 有约 3.0 TiB 空间，但服务器到 Hugging Face 的一次限时 HTTPS 探测超时，因此尚未下载，也未把网页展示的近似大小当作精确字节清单。恢复可用下载路径前，应再次核对修订和文件大小。

## 推荐的第一步

首个模型已确定为 DeepSeek-V2-Lite-Chat；Qwen3-8B 保留为低成本联调备选。ModelScope 模型与 Tokenizer 已固定到提交 `d174ca84ff4d8cd51f8e927bcb1242555e31b2c0` 并通过逐文件校验，不使用浮动的 `master` 作为实验标识。下一步仍需获授权后以 BF16、TP=1、较短的最大上下文进行功能验证，之后再建立多组输入/输出长度与并发度的工作负载。具体服务参数应以服务器上的 vLLM `0.32.0` 帮助信息和可用显存为准，不能直接照搬其他版本文档。

工作负载至少分为短输入/短输出、长输入/短输出、短输入/长输出三类；这三类分别更容易揭示交互延迟、Prefill 与 Decode 差异。每组记录输入/输出 Token 数、并发、请求到达过程、随机种子、预热、重复次数和失败请求。先做正确性与请求完整性检查，再比较性能。

`configs/m1-workload-plan.json` 只是待审阅的目标 Token 数与并发组合，模型字段暂为空；没有生成真实请求，也没有通过 Tokenizer 验证实际长度。若模型不可用或显存不足，应调整计划，不能把目标值写成实测值。

TTFT 从客户端发送请求到收到首个流式输出计时；TPOT 按每个请求的“总延迟减 TTFT，再除以输出 Token 数减 1”计算。ITL 是相邻流式输出的间隔，不能与 TPOT 混用。vLLM 官方文档还指出重复请求可能命中 Prefix Cache，因此基线必须记录缓存设置，并在需要独立重复时重启服务、变更种子或清理缓存。

`benchmarks/metrics.py` 实现纯 CPU 指标公式并由 `tests/unit/test_metrics.py` 覆盖常见边界。ITL 仅针对实际收到的非空流式输出事件；一个事件若携带多个 Token，不能虚构其内部 Token 的时间间隔。只有服务端返回可靠的输入/输出 Token 计数后，才能据此计算真实 TPOT。

## 本轮不执行的操作

目前仅完成小张量 Smoke Test。未下载权重、未启动 vLLM、未测量 TTFT/TPOT/吞吐量，也未取得后续模型实验的 GPU 授权。下一次执行前需确认模型、下载/磁盘预算、GPU 编号和使用时间窗口，并重新检查占用。

## 资料

- [Qwen3-8B 模型卡](https://huggingface.co/Qwen/Qwen3-8B)
- [Qwen3-32B 模型卡](https://huggingface.co/Qwen/Qwen3-32B)
- [Qwen3-30B-A3B-Instruct-2507 模型卡](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507)
- [vLLM Benchmark CLI 与指标定义](https://docs.vllm.ai/en/stable/benchmarking/cli/)
