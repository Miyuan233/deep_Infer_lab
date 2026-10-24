# DeepInfer-H200-Lab

这是一个面向 H200 的大模型推理优化实验室。目标是形成可复现的 L4 成果：完成 Kernel 级优化，将其接入真实推理路径，并进行端到端验证。

阅读顺序：

- `AGENTS.md`：安全约束与工程规则；
- `PROJECT.md`：范围、里程碑和测量方法；
- `PROGRESS.md`：当前已验证状态与下一步；
- `docs/environment.md`：M0 环境审计。

指定 Conda 环境为 `infer-h200`。自动化命令优先采用：

```bash
$HOME/anaconda3/bin/conda run -n infer-h200 <命令>
```

在用户明确授权 GPU 编号前，不得使用任何 GPU。
