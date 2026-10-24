# 项目进度

最后更新：2026-10-24（Asia/Shanghai）

## 当前阶段

M1 单卡基线准备——模型权重已固定并校验，首次离线加载及短文本生成功能验证通过；尚未启动服务或进行性能基准。

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
- 只读检查发现用户目录暂无 Hugging Face/ModelScope 模型缓存，也未发现 Environment Module；形成 `docs/m1-baseline-plan.md`。最初考虑 Qwen3-8B 做测量链联调，后因项目目标进一步比较了 DeepSeek 系模型。
- 已核对 DeepInfer 官方 README 与部署问答：当前公开版列出 NVIDIA SM100 与 DeepSeek-V4.1-Flash，不能视作 H200（SM90）/DeepSeek-V2-Lite-Chat 可直接运行；制定 `docs/deepinfer-reading-plan.md`，从 M1 并行研读，待 M2 证据决定是否迁移组件。
- 确认 Qwen3-8B 官方文件页当前修订为 `b968826d9c46dd6066d109eabc6255188de91218`、仓库约 16.4 GB；服务器对 Hugging Face 的 IPv4 HTTPS 连接超时。该备选模型尚未下载。
- 新增纯 CPU 的 TTFT/TPOT/ITL 指标公式与 7 项单元测试，以及仅供审阅的 M1 工作负载目标配置；尚未连接推理服务或产出基准数据。
- 用户询问是否存在更适合 DeepInfer 目标的模型，因此暂停 Qwen3-8B 下载决策。只读比较 DeepSeek-V2-Lite-Chat、Qwen3-8B 与 Qwen3-30B-A3B-Instruct-2507；用户最终选择 DeepSeek-V2-Lite-Chat，详见 `docs/m1-model-comparison.md`。
- 用户单独批准约 31.4 GB 模型下载。使用项目独立 `.venv/` 内的 `modelscope-hub==0.4.6` 从 ModelScope 固定提交 `d174ca84ff4d8cd51f8e927bcb1242555e31b2c0` 下载；16 个文件共 31,418,838,137 字节。2026-10-24 16:44（Asia/Shanghai）独立校验全部文件大小与 SHA-256，通过 16/16；原始校验 JSON 保留在服务器本地 `models/DeepSeek-V2-Lite-Chat/verification.json`。下载和校验未使用 GPU。
- 新增模型清单、独立校验器与 6 项相关 CPU 单元测试；服务器 `infer-h200` 全套 18 项 CPU 单元测试通过。模型、下载器和原始校验文件均被 Git 忽略；`infer-h200` 的 `pip check` 仍显示无依赖破损。
- 在禁用可见 GPU 的 CPU 进程中解析已校验的 Tokenizer、模型配置和权重索引：Tokenizer 词表 100002，BF16，`DeepseekV2ForCausalLM`，索引指向全部 4 个预期权重分片；制定 `docs/m1-first-load-plan.md`，等待下一次 GPU 授权。
- 用户单独授权 GPU 3 进行最多 15 分钟、预计 60–75 GiB 的离线模型功能验证。2026-10-24 17:03（Asia/Shanghai）运行前 GPU 3 为 0 MiB、无计算进程；以 UUID 限定可见设备，vLLM `0.32.0` 在 BF16、TP=1、`gpu_memory_utilization=0.45`、`max_model_len=4096`、`max_num_seqs=4`、`enforce_eager=True` 下成功加载模型并生成 32 个 Token。脚本状态 `passed`，总耗时 48.407 秒；`finish_reason=length`，回答在 32 Token 上限处被截断。退出后 GPU 3 回到 0 MiB、无计算进程。原始结果和日志保存在服务器本地 `results/m1/20261024T090313Z-first-load/`，运行代码提交 `e273ffb`；详见 `docs/m1-first-load-result.md`。

## 当前重要观察

- `nvidia-smi` 的 CUDA UMD 13.4 不等于已安装系统级 CUDA Toolkit。
- PyTorch 自带 CUDA 13.2 Runtime。环境外 PATH 中虽无 `nvcc`，但 Wheel 内有 `nvcc` 13.4.92；能否可靠构建自定义扩展，仍需验证混合版本、Header 和链接器布局。
- Triton 已在获授权的 GPU 3 上完成 H200 JIT Launch 与最小正确性验证；这不代表任何 Kernel 加速或模型推理性能结论。
- M0 检查未在 `infer-h200` 中发现 `pytest`、`flash-attn` 或 Nsight 命令行工具；模型下载器只安装在项目独立 `.venv/`，未更改 `infer-h200` 依赖。
- GPU 3 的两次授权分别只覆盖已完成的 Smoke Test 和短时离线模型功能验证；后续服务、Benchmark 或 Profiler 仍需单独确认资源预算与授权。
- 首次模型加载虽成功，vLLM 仍报告部分 FlashInfer Kernel 因预编译包或编译工具缺失而禁用，并采用 Triton MoE 后端；这可能影响后续性能基线，不能从功能验证推断最优性能。
- 目录在初始化前不是 Git 仓库。

## 阻塞项与待决策

1. 后续服务、Benchmark 或 Profiler Capture 前，用户必须明确授权 GPU 编号；本次短时功能验证授权不自动延续。
2. 首次离线加载已通过；正式基线前仍需确定服务暴露方式、请求工作负载、显存采样方法和安全余量。
3. 决定如何暴露并验证环境内的 Wheel 版 `nvcc`，以及如何在不修改系统的情况下获得 Nsight；同时应确认管理员是否提供 Module。
4. 决定把 `pytest` 等开发依赖安装到 `infer-h200`，还是克隆一个更严格隔离的项目环境。

## 下一步

1. 按 `docs/deepinfer-reading-plan.md` 研读官方架构，记录与单卡 H200 基线的可迁移点和不可迁移点。
2. 在不使用 GPU 的前提下确定服务与负载设计：请求长度、到达过程、并发度、预热/冷启动边界、重复次数及显存采样方法。
3. 制定可复现的 TTFT、TPOT/ITL、吞吐量和显存基线方案，保存逐请求原始数据；实际服务和 GPU Benchmark 另行申请 GPU 编号与资源预算。

## 性能结论

无。Smoke Test 只验证 PyTorch/Triton 小张量正确性；3.944 秒不能用作推理或 Kernel 性能指标。首次模型加载记录的 48.407 秒包含启动、加载和生成，不含记录后清理时间，仅证明功能可用，不是 TTFT、TPOT、吞吐量或峰值显存数据；日志中的估算生成速度也不能作为基线结果。Smoke Test JSON 中的 2.0 MiB 仅是 PyTorch 报告的显存保留峰值，不是 GPU 实际峰值。
