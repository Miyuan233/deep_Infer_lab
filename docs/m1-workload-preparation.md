# M1 离线请求准备结果

日期：2026-10-25（Asia/Shanghai）

## 做了什么

在服务器 `infer-h200` 环境中强制离线、禁用可见 GPU，使用已校验的 DeepSeek-V2-Lite-Chat 本地 Tokenizer，按 `configs/m1-workload-plan.json` 生成 24 条合成聊天请求。三组各 8 条，输入的唯一实验编号放在背景正文前，避免全部请求具有长篇相同前缀。此步骤没有加载模型权重、启动服务或测量推理性能。

| 分组 | 目标输入 Token | 实际输入 Token | 未来输出上限 | 计划并发 |
| --- | ---: | ---: | ---: | --- |
| 短输入短输出 | 128 | 131（8 条相同） | 128 | 1、4 |
| 长输入短输出 | 2048 | 2063（8 条相同） | 128 | 1、4 |
| 短输入长输出 | 128 | 132（8 条相同） | 512 | 1、4 |

“未来输出上限”只是请求中的 `max_tokens`，不是已测得的输出长度。输入长度通过 `apply_chat_template(..., tokenize=True, add_generation_prompt=True)` 返回的 `input_ids` 计数；不能对整个 `BatchEncoding` 调用 `len`，那只会得到字段数量。

## 原始产物与复现

- 服务器目录：`results/m1/20261025T114455Z-workload-prep/`，包含 `requests.jsonl` 和 `manifest.json`，不提交公开 Git。
- 生成代码提交：`fa94ee9e471b952cdb421371050be6afd600216b`。
- 模型修订：`d174ca84ff4d8cd51f8e927bcb1242555e31b2c0`；Tokenizer 文件 SHA-256 与配置哈希见原始 `manifest.json`。
- `requests.jsonl` SHA-256：`4d54a7ac60cb38f61922b2d7325e4bf272e9e62c31ddfca74e53ec3eb2d5f0ad`；独立重读确认 24 行、24 个唯一请求 ID，逐条重算的输入 Token 数全部一致。
- 复现命令：在项目目录执行 `CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 $HOME/anaconda3/envs/infer-h200/bin/python scripts/prepare_m1_workload.py --output-dir results/m1/<新的UTC时间戳>-workload-prep --samples-per-group 8`。结果目录必须是新目录，避免覆盖原始数据。

## 使用边界与学习练习

这些请求由重复的技术背景合成，适合先验证不同输入/输出长度下的测量链，却不一定代表真实用户请求分布。正式基线前应审阅语义内容，并决定是否补充自然请求；还需固定 Prefix Cache 设置、到达过程、并发、预热和重复次数。

建议亲自打开一条 `requests.jsonl`，解释 `target_input_tokens` 与 `input_tokens` 为什么不同、`max_tokens` 为什么不等于实际输出；再试着修改一个背景句子，预测并用 Tokenizer 验证长度会如何变化。修改请求后必须生成新的不可变结果目录，不得覆盖本次产物。
