# Project v1 Summary

## v1 完成内容

- 创建项目目录结构。
- 构造 10 类电商售后 SFT 数据。
- 生成 300 条 JSONL 样本。
- 划分 train 240 / eval 60。
- 转换为 MiniMind `conversations` 格式。
- 完成数据 smoke test。
- 完成 Python / CUDA / GPU 环境检查。
- 准备 MiniMind `full_sft_768.pth` baseline checkpoint。
- 完成 baseline 推理与分析。
- 完成 MiniMind LoRA 微调。
- 完成 LoRA 推理。
- 完成 baseline vs LoRA before/after 对比。
- 完成 final LoRA analysis。

## 关键结果

- base checkpoint：`full_sft_768.pth`
- LoRA adapter：`lora_customer_service_768.pth`
- adapter size：约 0.76 MB
- loss：3.7383 -> 2.8888
- baseline prompts：10 条
- before/after 对比：已完成

工程上，v1 已完整跑通低资源 LoRA 微调闭环。

## 主要不足

- 数据规模较小，仅约 300 条。
- 测试集只有 10 条，覆盖不充分。
- LoRA 后业务效果提升有限。
- 礼貌安抚没有明显增强。
- 对违规请求仍未稳定拒绝。
- 小模型能力有限，仍出现泛化、偏题和重复。
- 自动评价主要基于关键词，不能替代人工评测。

## 下一阶段 v2 计划

- 扩展到 1000+ 高质量售后样本。
- 增加拒答边界、隐私保护、虚假退款等 hard cases。
- 增加多轮售后对话数据。
- 建立更系统的人工评分维度。
- 引入 LLM-as-Judge 辅助评估。
- 迁移到 Qwen-0.5B / Qwen-1.5B LoRA。
- 对比 MiniMind 与 Qwen 在同一数据集上的效果差异。
