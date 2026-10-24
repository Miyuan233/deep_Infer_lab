# M1 首次离线加载功能验证结果

日期：2026-10-24 17:03–17:04（Asia/Shanghai）  
性质：功能验证，不是性能 Benchmark。

## 结果

- 状态：`passed`。vLLM 成功加载 DeepSeek-V2-Lite-Chat，并对一个中文提示生成 32 个 Token。
- `finish_reason=length`：回答触及预设的 32 Token 上限而截断；这不表示模型自然完成了回答，也不影响“能够生成”的功能结论。
- 结果写入时已耗时 48.407 秒，包含启动、模型加载和生成，不含其后的清理时间，不用于推理性能比较。
- 结束后 `nvidia-smi` 显示 GPU 3 为 0 MiB，且无计算进程。GPU 0–2 的已有进程未被触碰。
- 没有启动在线服务、运行 Benchmark 或采集 Profiler。

## 可复现条件

- 授权设备：`nvidia-smi` GPU 3，UUID `GPU-a115747e-47cf-2688-09a9-c3bb00184928`；运行前 0 MiB、无计算进程，PyTorch 仅看到这一张 H200。
- 代码：`e273ffb6185fae8155110c34e99f123af5fccb9a`；模型：ModelScope 固定修订 `d174ca84ff4d8cd51f8e927bcb1242555e31b2c0`，已逐文件校验。
- 环境：`infer-h200`，PyTorch `2.13.0+cu132`，vLLM `0.32.0`。
- 参数：BF16、TP=1、`gpu_memory_utilization=0.45`、`max_model_len=4096`、`max_num_seqs=4`、`enforce_eager=True`；贪心生成、最多 32 Token；`CUDA_VISIBLE_DEVICES` 限定为 GPU UUID，Hugging Face 和 Transformers 均设为离线。
- 执行脚本：`scripts/m1_first_load.py`；命令由 `timeout --signal=TERM --kill-after=30s 15m` 限时。
- 原始结果：服务器本地 `results/m1/20261024T090313Z-first-load/result.json` 与 `raw.log`，不提交公开 Git。

## 解释与限制

日志报告权重加载约 29.32 GiB，vLLM 为 KV Cache 计算出约 31.85 GiB 可用空间；这些是引擎内部日志数值，不是经外部采样的实际 GPU 峰值。此次没有高频显存采样，不报告峰值显存。

vLLM 日志提示部分 FlashInfer Kernel 因缺少预编译包或 `nvcc`/`ninja` 路径而禁用，同时明确选择 `TRITON` Unquantized MoE 后端。功能能够跑通，但不能据此判断当前 Kernel 组合的性能最优。下一阶段应先固定服务参数和请求分布，再单独授权 GPU 做可重复的端到端基线。
