# 项目进度

最后更新：2026-10-24（Asia/Shanghai）

## 当前阶段

M1 前置验证准备——等待用户授权具体 GPU 编号。

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
- 编写显式指定 GPU 编号的 PyTorch/Triton Smoke Test、CPU 侧安全检查测试及中文执行说明；尚未进行 GPU 运行。

## 当前重要观察

- `nvidia-smi` 的 CUDA UMD 13.4 不等于已安装系统级 CUDA Toolkit。
- PyTorch 自带 CUDA 13.2 Runtime。环境外 PATH 中虽无 `nvcc`，但 Wheel 内有 `nvcc` 13.4.92；能否可靠构建自定义扩展，仍需验证混合版本、Header 和链接器布局。
- Triton 已安装并携带 `ptxas` 12.8.93，但因尚未授权 GPU，未进行 H200 JIT Launch 验证。
- M0 检查未在 `infer-h200` 中发现 `pytest`、`flash-attn` 或 Nsight 命令行工具；尚未安装任何包。
- GPU 3 在检查时无进程，但“空闲”不代表“已授权”。
- 目录在初始化前不是 Git 仓库。

## 阻塞项与待决策

1. 任何 CUDA 初始化、模型加载、Benchmark 或 Profiler Capture 前，用户必须明确授权 GPU 编号。
2. 必须先估算下载大小和显存余量，再选择基线模型与工作负载。
3. 决定如何暴露并验证环境内的 Wheel 版 `nvcc`，以及如何在不修改系统的情况下获得 Nsight；同时应确认管理员是否提供 Module。
4. 决定把 `pytest` 等开发依赖安装到 `infer-h200`，还是克隆一个更严格隔离的项目环境。

## 下一步

1. 审阅 M0 文档与环境快照。
2. 用户确认 GPU 编号和可接受的测试时间窗口。
3. 获授权后执行预计 1～2 分钟的 Smoke Test：CUDA 可用性、设备能力、微小 Tensor 正确性、Triton JIT 与显存释放。
4. 只读检查 Environment Module 和用户态 CUDA/Nsight 方案。
5. 提出 2～3 个基线模型/工作负载组合，列出下载大小、预计显存和研究价值。
6. 获批后固定依赖与模型版本，开始实现 M1 Benchmark Harness。

## 性能结论

无。M0 没有运行模型推理、训练、GPU Benchmark 或 Profiler Capture。
