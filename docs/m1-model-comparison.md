# M1 首个模型的选择记录（待用户确认）

## 决策问题

项目目标是学习 DeepInfer 架构并在单张 H200 上完成可解释的 L4 推理优化。因此首个模型不只要“能跑”，还应提供值得分析的真实注意力、MoE 或调度路径；同时必须给正确性和端到端基线留出显存余量。

| 模型 | 架构与用途 | ModelScope 仓库字节数 | 当前判断 |
| --- | --- | ---: | --- |
| [DeepSeek-V2-Lite-Chat](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat) | 16B 总参数、2.4B 激活参数；MLA + DeepSeekMoE | 31,418,838,137（约 31.4 GB） | **推荐作为主模型候选**：最贴合本项目的 MLA/MoE 学习目标 |
| [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) | 8.2B dense；先跑通服务与测量链 | 16,397,461,896（约 16.4 GB） | 低成本联调备选，但不能代表 MoE/MLA 热点 |
| [Qwen3-30B-A3B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507) | 30.5B 总参数、3.3B 激活参数；MoE + GQA | 61,084,263,662（约 61.1 GB） | 适合作为后续现代 MoE 对照，但权重与下载成本更高，且无 MLA |

字节数来自 2026-10-24 对各模型 ModelScope `repo/files` 元数据的只读查询；不是已经下载的文件，也不能代替磁盘上的 SHA-256 验证。`/home` 当时约有 3.0 TiB 可用空间。模型显存除权重外还包括 KV Cache、工作区与框架开销；此表不能保证任一模型在当前服务配置下成功加载。

## 推荐依据与风险

- DeepSeek 官方[模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat)说明 V2 Lite 可在单张 40G GPU 上部署，并明确其 MLA 与 MoE 架构。这个说法来自上游，不是本项目实测。
- [vLLM 支持模型文档](https://docs.vllm.ai/en/stable/models/supported_models/)列出 `DeepseekV2ForCausalLM`；服务器安装的 vLLM `0.32.0` 源码也注册了此类并包含 `deepseek_v2.py`。这只证明有代码路径，尚未证明 H200 上的加载、数值和性能均正常。
- DeepSeek-V2-Lite-Chat 使用 DeepSeek 模型许可证，不同于 Qwen3 的 Apache-2.0。公开代码、权重和实验材料前须分别核对许可条件；原始权重不进入本项目 Git 仓库。
- DeepInfer 当前公开版仍只列出 SM100 与 DeepSeek-V4.1-Flash，不能因为选择了 V2 Lite 就声称可以直接运行 DeepInfer。V2 Lite 的价值是让我们在 vLLM 上研究相近的 MLA/MoE 问题，并在 Profiling 后挑选可迁移的设计。

## 尚未决策或执行

用户提出是否有更适合模型后，Qwen3-8B 下载计划已暂停。需要用户明确选择模型与下载预算。之后先固定 ModelScope 修订、校验清单与磁盘余量，再下载到服务器的非 Git 目录。模型加载、服务和基准需要另行确认 GPU 编号、预计显存和时间窗口，并在执行前重新检查 GPU 占用。
