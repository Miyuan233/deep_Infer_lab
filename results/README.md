# 实验结果规范

`results/` 保存实验依据，不是临时目录。一次运行结束后，不得修改原始测量数据。

建议结构：

```text
results/
  <阶段>/
    <YYYYMMDDTHHMMSSZ>-<实验名称>/
      manifest.yaml
      command.txt
      environment/
      raw/
      summary/
      correctness/
      profiler/
```

`manifest.yaml` 必须记录授权 GPU 编号/UUID、Git 状态、模型与 Tokenizer 版本、工作负载、预热、重复次数、Engine 参数，以及相对基线的全部有意差异。

大型 Profiler 二进制和模型文件不进入 Git。必须保存其校验和、路径、工具版本、Capture 命令和可读导出结果，保证证据可追溯。

既有 `gpu-environment.txt`、`python-version.txt` 和 `m0/` 快照保存在服务器本地。它们可能含有主机身份或其他用户进程信息，因此不提交到公开仓库；需要复现实验时可在获授权的环境中查阅。
