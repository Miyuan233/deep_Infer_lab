# 项目进度

最后更新：2026-10-24（Asia/Shanghai）

## 当前阶段

M1 基线方案设计——GPU 3 的一次性前置 Smoke Test 已完成；尚未开始模型推理或性能基准。

## 已完成

- 确认远端主机为 Debian GNU/Linux 13，内核 `6.12.111+deb13-amd64`；具体主机名与用户名仅保存在服务器本地的 M0 快照中。
- 确认双路 CPU，每路 96 个物理核心、SMT2，共 384 个逻辑 CPU 和两个 NUMA Node。
- 确认系统内存 503 GiB；检查时 `/home` 约有 3.0 TiB 可用空间。
- 确认 4 张 NVIDIA H200 NVL，每张报告 143771 MiB；驱动/KMD 为 `615.71.09`，CUDA UMD 为 `13.4`。
- 确认任意两张 GPU 之间均显示 `NV6`，所有 GPU 位于 NUMA Node 0。
- 检查时 GPU 0、1、2 上存在其他任务；未修改或干扰任何进程。
- 定位 Anaconda：`$HOME/anaconda3`，Conda 版本 `25.11.0`。
- 纠正环境名称：服务器中实际存在的是 `infer-h200`，不是 `infer-200`。
- 审计 `infer-h200`：Python 3.12.15、PyTorch 2.13.0+cu132、vLLM 0.32.0、Triton 3.7.1、Transformers 5.19.0、NumPy 2.3.5；`pip check` 未发现依赖破损。
- 确认 PyTorch 基于 CUDA 13.2 构建，报告 cuDNN 9.20.0，架构列表包含 H200/Hopper 所需的 `sm_90`。
- 确认 `nvcc`、`nsys`、`ncu` 不在 PATH；未找到 `/usr/local/cuda*` 或 `/opt/nvidia/nsight*`。
- 在 `infer-h200` 内找到用户态 CUDA 组件：NVIDIA Wheel 提供的 `nvcc` 13.4.92 与 `ptxas`，以及 Triton 自带的 `ptxas` 12.8.93；环境还包含 `cuda-toolkit==13.2.1` 与 `nvidia-nccl-cu13==2.29.7`。
- 确认目标目录原先已有标准空目录和三个早期快照文件。
- 发现 `configs/requirements-initial.txt` 来自 Conda `base`，而非 `infer-h200`；该文件仅作为历史证据保留，不得用于重建项目环境。
- 创建项目文档、目录、环境采集脚本和 Git 仓库。
- 将项目同步到公开 GitHub 仓库 `Miyuan233/deep_Infer_lab`；H200 与本地 `main` 均跟踪 `origin/main`，首次提交为 `b10e70a`。
- 将含内部主机身份、进程信息的 M0 快照及历史 `base` 清单排除在公开提交之外，原始文件保留在服务器。
- 生成轻量级 M0 环境快照：`results/m0/20261024T044101Z-environment/`；其中包含本机身份与进程信息，仅保存在服务器，不提交到公开仓库。
- 编写显式指定 GPU 编号的 PyTorch/Triton Smoke Test、CPU 侧安全检查测试及中文执行说明；5 项 CPU 侧单元测试通过。
- 用户明确授权本次 Smoke Test 使用 GPU 3。执行前复查为 0 MiB 已用、无计算进程；1024 个 FP32 元素的 PyTorch/Triton 加法结果完全一致，状态 `passed`，耗时 3.944 秒。结束后复查 GPU 3 为 0 MiB、无计算进程。原始 JSON 保存在服务器本地 `results/m0/20261024T075614Z-gpu-smoke-gpu3/result.json`，对应代码提交 `5458798`。
- 只读检查发现用户目录暂无 Hugging Face/ModelScope 模型缓存，也未发现 Environment Module；形成 `docs/m1-baseline-plan.md`，暂推荐先用 Qwen3-8B 验证测量链，再评估更大 dense 或 MoE 模型。
- 已核对 DeepInfer 官方 README 与部署问答：当前公开版列出 NVIDIA SM100 与 DeepSeek-V4.1-Flash，不能视作 H200（SM90）/Qwen3-8B 可直接运行；制定 `docs/deepinfer-reading-plan.md`，从 M1 并行研读，待 M2 证据决定是否迁移组件。
- 确认 Qwen3-8B 官方文件页当前修订为 `b968826d9c46dd6066d109eabc6255188de91218`、仓库约 16.4 GB；`/home` 约 3.0 TiB 可用，但服务器对 Hugging Face 的 IPv4 HTTPS 连接超时，尚未下载权重。
- 新增纯 CPU 的 TTFT/TPOT/ITL 指标公式与 7 项单元测试，以及仅供审阅的 M1 工作负载目标配置；尚未连接推理服务或产出基准数据。

## 当前重要观察

- `nvidia-smi` 的 CUDA UMD 13.4 不等于已安装系统级 CUDA Toolkit。
- PyTorch 自带 CUDA 13.2 Runtime。环境外 PATH 中虽无 `nvcc`，但 Wheel 内有 `nvcc` 13.4.92；能否可靠构建自定义扩展，仍需验证混合版本、Header 和链接器布局。
- Triton 已在获授权的 GPU 3 上完成 H200 JIT Launch 与最小正确性验证；这不代表任何 Kernel 加速或模型推理性能结论。
- M0 检查未在 `infer-h200` 中发现 `pytest`、`flash-attn` 或 Nsight 命令行工具；尚未安装任何包。
- GPU 3 的授权仅针对已完成的本次 Smoke Test；后续模型加载、服务和 Benchmark 仍需单独确认资源预算与授权。
- 目录在初始化前不是 Git 仓库。

## 阻塞项与待决策

1. 后续 CUDA 初始化、模型加载、Benchmark 或 Profiler Capture 前，用户必须明确授权 GPU 编号；本次 Smoke Test 授权不自动延续。
2. 必须先估算下载大小和显存余量，再选择基线模型与工作负载。
3. 决定如何暴露并验证环境内的 Wheel 版 `nvcc`，以及如何在不修改系统的情况下获得 Nsight；同时应确认管理员是否提供 Module。
4. 决定把 `pytest` 等开发依赖安装到 `infer-h200`，还是克隆一个更严格隔离的项目环境。

## 下一步

1. 只读检查 Environment Module 和用户态 CUDA/Nsight 方案。
2. 用户确认基线模型及下载预算；下载前核对精确权重版本、文件字节数与磁盘余量。
3. 按 `docs/deepinfer-reading-plan.md` 研读官方架构，并记录与单卡 H200 基线的可迁移点和不可迁移点。
4. 获批后固定依赖与模型版本，开始实现 M1 Benchmark Harness；先规定正确性、TTFT、TPOT、吞吐量和显存的测量口径。
5. 模型下载、加载和任何 Benchmark 运行前，重新确认 GPU 编号、资源预算和时间窗口。

## 性能结论

无。已运行的 Smoke Test 只验证 PyTorch/Triton 小张量正确性；3.944 秒是包含启动与编译等开销的脚本总耗时，不能用作推理或 Kernel 性能指标。JSON 中的 2.0 MiB 是 PyTorch 报告的显存保留峰值，不包含 CUDA 上下文等进程总占用，不能当作 GPU 实际峰值。
