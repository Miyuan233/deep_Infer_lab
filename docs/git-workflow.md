# Git 工作流

项目的 GitHub 远端为 `git@github.com:Miyuan233/deep_Infer_lab.git`，`main` 分支在本地与 H200 上都跟踪 `origin/main`。仓库是公开的，提交前应检查暂存清单中是否含凭据、内部地址、其他用户的进程信息或模型权重。

## 日常步骤

进入项目目录后，先检查并同步：

```bash
git status --short --branch
git pull --ff-only
```

完成一项可验证的工作后，更新 `PROGRESS.md`，只暂存本次相关文件，检查再提交：

```bash
git add AGENTS.md PROJECT.md PROGRESS.md docs/ scripts/ tests/
git diff --cached --check
git diff --cached --stat
git commit -m "说明本次改动"
git push
```

上面的 `git add` 仅是示例，应按实际改动调整路径。若 `git pull --ff-only` 因分叉而失败，先检查两端提交和工作区状态，再决定合并方式；不要用强制推送覆盖已有历史。

## 实验数据

- 代码、配置、中文文档、可公开且体积适中的结果摘要可以提交。
- 每次 Benchmark 的原始输出必须保存在服务器 `results/` 中，并与配置、时间戳、Git Commit 和 GPU 编号关联。
- M0 原始环境快照、历史 `base` 清单和包含其他用户进程信息的文件已被 `.gitignore` 排除，仅保存在服务器本地。
- 模型权重、大型 Profiler 文件和敏感数据不进入公开 Git 仓库；用路径、校验和及命令记录其来源。

Git 记录代码与实验配置的演进；服务器磁盘承载未公开的大型原始产物。重要结果还应有独立备份，GitHub 仓库本身不能代替全部实验数据备份。
