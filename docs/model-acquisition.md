# DeepSeek-V2-Lite-Chat 模型获取与校验

## 已批准的范围

用户确认首个基线模型为 `deepseek-ai/DeepSeek-V2-Lite-Chat`，并单独批准从 ModelScope 下载约 31.4 GB。此授权只覆盖模型下载，不覆盖 GPU 初始化、模型加载、服务启动或 Benchmark。

H200 服务器无法直连 Hugging Face，ModelScope 的该官方模型仓库可访问。为避免浮动的 `master`，先用 `git ls-remote` 取得 ModelScope 提交 `d174ca84ff4d8cd51f8e927bcb1242555e31b2c0`，再以该提交号查询 ModelScope 文件 API。16 个文件共 31,418,838,137 字节，清单及各文件 SHA-256 保存在 `configs/deepseek-v2-lite-chat-modelscope-manifest.json`。

四个权重分片的 SHA-256 又分别与 DeepSeek 官方 Hugging Face 文件页核对一致：[分片 1](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat/blob/main/model-00001-of-000004.safetensors)、[分片 2](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat/blob/main/model-00002-of-000004.safetensors)、[分片 3](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat/blob/main/model-00003-of-000004.safetensors)、[分片 4](https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite-Chat/blob/main/model-00004-of-000004.safetensors)。这只是远端清单的交叉核对，不能代替本地文件哈希验证。

## 隔离方式

- 模型保存在服务器项目目录 `models/DeepSeek-V2-Lite-Chat/`，`models/` 被 Git 忽略；绝不提交权重。
- 下载器是单独装在项目 `.venv/` 中的 `modelscope-hub==0.4.6`；`.venv/` 被 Git 忽略。推理用的 `infer-h200` Conda 环境未因下载器安装而改变。
- 下载命令固定修订并限制为两个并发下载任务；不会使用 GPU：

```bash
./.venv/bin/ms-hub download deepseek-ai/DeepSeek-V2-Lite-Chat \
  --revision d174ca84ff4d8cd51f8e927bcb1242555e31b2c0 \
  --local-dir ./models/DeepSeek-V2-Lite-Chat \
  --max-workers 2
```

## 验证门槛

下载器报告成功后，还需运行项目独立校验器：

```bash
$HOME/anaconda3/bin/conda run -n infer-h200 python scripts/verify_model_snapshot.py \
  --model-dir models/DeepSeek-V2-Lite-Chat \
  --manifest configs/deepseek-v2-lite-chat-modelscope-manifest.json
```

只有 16 个文件的大小、SHA-256 均符合固定清单，才能称为“权重下载并校验完成”。这仍不能说明模型在 H200 上可运行或有任何性能结论。后续加载前必须获得具体 GPU 编号授权并重新检查占用。

## 2026-10-24 实际结果

- ModelScope 下载器以退出码 0 结束，报告固定提交的 16/16 个文件已下载。
- 2026-10-24 16:44（Asia/Shanghai）运行独立校验器，结果 `passed`：16/16 个文件的大小和 SHA-256 全部符合清单，验证字节数为 31,418,838,137。
- 原始校验结果保留在服务器本地 `models/DeepSeek-V2-Lite-Chat/verification.json`；模型、校验结果与下载器目录均被 Git 忽略。下载后 `/home` 约剩 4.7 TiB 空间，`infer-h200` 的 `pip check` 未发现依赖破损。
- 没有加载模型、启动推理服务或使用 GPU。此前 GPU 3 的 Smoke Test 授权不适用于下一次模型实验。
