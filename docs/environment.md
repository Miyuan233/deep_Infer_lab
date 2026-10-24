# M0 环境审计

检查时间：2026-10-24（Asia/Shanghai）。本文是时间点快照，不保证资源以后仍保持相同状态。

## 主机

- 主机名与用户名：保存在服务器本地的 M0 原始快照中，不公开提交
- OS：Debian GNU/Linux 13（trixie）
- Kernel：`6.12.111+deb13-amd64`
- CPU：双路 AMD EPYC 9J14，每路 96 核，SMT2，共 384 个逻辑 CPU
- NUMA：2 个 Node；GPU 的 PCIe 局部性位于 NUMA Node 0
- 内存：总计 503 GiB；检查时可用 417 GiB
- Home 文件系统：总计 6.5 TiB；检查时约 3.0 TiB 可用

## GPU 与拓扑

- 4 × NVIDIA H200 NVL
- 每张 GPU 报告显存：143771 MiB
- 驱动/KMD：615.71.09
- `nvidia-smi` 报告 CUDA UMD：13.4
- MIG：Disabled
- 任意两张 GPU 之间均显示 `NV6`
- 检查时 GPU 0、1、2 上已有计算进程，GPU 3 没有进程

本次审计没有启动 CUDA 工作，也没有修改任何进程。看似空闲的 GPU 不等于已获授权。

## Conda 与 Python

- Anaconda 根目录：`$HOME/anaconda3`
- Conda：25.11.0
- 已发现环境：`base`、`diffcast`、`infer-h200`
- 项目环境：`infer-h200`
- Python：3.12.15

`infer-h200` 关键软件：

| 软件 | 版本/状态 |
| --- | --- |
| PyTorch | 2.13.0+cu132 |
| PyTorch CUDA Build | 13.2 |
| PyTorch 报告的 cuDNN | 9.20.0 |
| vLLM | 0.32.0 |
| Triton | 3.7.1 |
| Transformers | 5.19.0 |
| NumPy | 2.3.5 |
| flash-attn | 未发现 |
| pytest | 未发现 |

`python -m pip check` 未发现依赖破损。

## 工具链状态

系统 PATH 中可用：

- `nvidia-smi`
- CMake 3.31.6
- GCC/G++ 14.2.0
- Git 2.47.3

初次检查时未在系统/环境 PATH 中找到：

- `nvcc`
- `nsys`
- `ncu`

未发现 `/usr/local/cuda*` 或 `/opt/nvidia/nsight*`。按已检查的包名，Debian 包查询也没有发现 CUDA Toolkit、Nsight 或 NCCL 系统包。

进一步检查发现 `infer-h200` 内安装了 Python Wheel 形式的 CUDA 组件：

- NVIDIA Wheel 的 `nvcc` 13.4.92：`site-packages/nvidia/cu13/bin/nvcc`；
- 同一 `nvidia/cu13` 目录中的 NVIDIA Wheel `ptxas`；
- Triton 自带的 `ptxas` 12.8.93、`cuobjdump` 和 `nvdisasm`；
- Python Distribution 中包含 `cuda-toolkit==13.2.1`、`nvidia-cuda-nvcc==13.4.92`、`nvidia-nccl-cu13==2.29.7`。

上述组件未加入 PATH。Header、Library Discovery 以及 12.8/13.2/13.4 混合版本兼容性尚未通过 Build 或 Device Launch 验证。

## 版本含义

以下三个版本承担不同角色：

1. 驱动/KMD `615.71.09`：已安装的 GPU 驱动版本。
2. `nvidia-smi` 中的 CUDA UMD `13.4`：驱动侧 CUDA 兼容能力，不代表系统安装了编译 Toolkit。
3. `torch 2.13.0+cu132`：PyTorch Wheel 面向/携带 CUDA 13.2 用户态 Runtime。

因此，已安装的 PyTorch/vLLM Wheel 可能在没有系统 CUDA Toolkit 的情况下运行。Wheel 内编译组件可能支持自定义 CUDA 扩展，但采用前必须进行受控的 Compile/Link Smoke Test；Triton 的编译路径也应在 GPU 获授权后用极小 JIT Launch 验证。

## 已知历史文件问题

`configs/requirements-initial.txt` 早于本次审计，内容来自 `base`（Python 3.13.9），不是 `infer-h200`。它不是本项目的有效 Lockfile，禁止按该文件安装环境。
