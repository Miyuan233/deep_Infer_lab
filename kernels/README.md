# Kernel 目录

- `triton/`：Triton 实现与调优元数据。
- `cuda/`：CUDA/C++ 实现与 Build 集成。

每个优化 Kernel 必须附带参考路径、Shape/Dtype 覆盖范围、数值误差阈值、正确性测试，以及可回退的 Dispatch 或 Feature Flag。
