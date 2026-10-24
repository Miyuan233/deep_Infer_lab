# M1 前置验证：单卡 Smoke Test

## 要回答的问题

M0 已确认软件包存在，但尚未证明它们能在获授权的 H200 上启动。这个短时检查只回答三个问题：

1. 指定 GPU 是否确实空闲且有足够显存余量？
2. PyTorch 能否识别 H200 并完成一个很小的 CUDA 张量计算？
3. Triton 能否 JIT 编译、启动向量加法 Kernel，并得到与 PyTorch 完全一致的结果？

这不是性能 Benchmark，输出中的耗时不能用于优化结论。

## 资源预算与安全边界

- GPU：仅使用用户明确授权的一个 `nvidia-smi` 编号；执行前重新检查编号与 UUID。
- 显存：预计峰值低于 2 GiB（含 PyTorch CUDA 上下文和 JIT 运行开销）；若预检查发现已有计算进程、已用显存超过 256 MiB 或可用显存不足 4 GiB，脚本拒绝运行。
- 时长：预计约 1～2 分钟，首次 Triton 编译可能使时间波动。
- 工作内容：1024 个 FP32 元素的 PyTorch 与 Triton 加法正确性检查；不加载模型或启动服务。
- 结果：保存到服务器本地 `results/m0/<UTC时间戳>-gpu-smoke-gpu<编号>/result.json`，不提交公开仓库。

脚本先通过 `nvidia-smi` 将获授权的编号解析为 UUID，再用该 UUID 设置 `CUDA_VISIBLE_DEVICES`。这样框架内部的 `cuda:0` 始终指向所选物理 GPU，避免把框架设备序号误认为 `nvidia-smi` 编号。

## 执行方式

得到用户对具体 GPU 编号的授权后，在服务器项目目录运行：

```bash
$HOME/anaconda3/bin/conda run -n infer-h200 python scripts/gpu_smoke.py --gpu-index <授权编号>
```

执行结束后再用 `nvidia-smi` 检查显存是否释放。即使脚本通过，也只能证明最小运行路径可用；模型选择、vLLM 服务、Profiler 和端到端 Benchmark 仍需分别验证。

## 2026-10-24 实际结果

- 用户仅授权本次 Smoke Test 使用 GPU 3；运行前检查为 0 MiB 已用、无计算进程，运行后再次检查也为 0 MiB、无计算进程。
- PyTorch `2.13.0+cu132`、Triton `3.7.1` 识别 NVIDIA H200 NVL（计算能力 9.0）；1024 个 FP32 元素的结果完全一致。
- 脚本状态为 `passed`，总耗时 3.944 秒。原始结果位于服务器本地 `results/m0/20261024T075614Z-gpu-smoke-gpu3/result.json`，对应提交 `5458798`。该原始文件包含设备 UUID，因此不推送到公开仓库。
- PyTorch 报告的峰值 `reserved` 为 2.0 MiB，仅反映其缓存分配器，不是进程占用的整卡显存峰值。此次没有持续监测实际峰值，也没有性能 Benchmark。

此授权已用于上述单次测试，不自动覆盖后续模型加载、推理服务或性能测试。
