# Project Overview

## One Page Summary

MiniMind-CustomerService-LoRA 是一个面向电商售后合规回复的低资源 SFT / LoRA 实验项目。

项目从合成客服数据构造开始。

第一阶段使用 MiniMind 跑通 LoRA 微调闭环。

第二阶段扩展数据并增强拒答边界。

第三阶段构造统一评估集和 rule-based rubric。

第四阶段迁移到 Qwen2.5-1.5B-Instruct。

第五阶段规划真实数据增强，但尚未下载真实大数据，也尚未训练。

## Main Story

本项目的主线是：

```text
低资源电商售后合规数据构造
-> MiniMind LoRA 跑通微调流程
-> 发现小模型能力边界
-> 迁移 Qwen2.5-1.5B-Instruct
-> Qwen LoRA 效果提升
-> rule-based evaluation 与失败案例分析
```

MiniMind 阶段的意义是验证完整工程链路。

它证明了数据构造、格式转换、训练、adapter 保存、推理和评估都能跑通。

但 MiniMind LoRA v2 的整体分数只有 5.645。

这说明小模型在复杂售后规则、拒答边界和自然表达上仍有明显限制。

Qwen 阶段的意义是验证更强基座模型的价值。

Qwen baseline 的整体分数为 6.275。

它已经超过 MiniMind LoRA v2。

Qwen LoRA v4 的整体分数进一步提升到 7.865。

## Version Comparison

| Version | Base Model | Data Size | Method | Eval Size | Main Result | Limitation |
| --- | --- | ---: | --- | ---: | --- | --- |
| MiniMind baseline | MiniMind full_sft_768 | 0 project fine-tune samples | Baseline inference | 100 | Overall score 5.025 | 未针对电商售后合规场景微调 |
| MiniMind LoRA v1 | MiniMind full_sft_768 | 240 train / 60 eval | LoRA | 100 | Overall score 5.375 | 数据量小，hard cases 不足 |
| MiniMind LoRA v2 | MiniMind full_sft_768 | 800 train / 200 eval | LoRA | 100 | Overall score 5.645 | 小模型能力仍有限 |
| Qwen baseline | Qwen2.5-1.5B-Instruct | 0 project fine-tune samples | Baseline inference | 100 | Overall score 6.275 | 未经过项目客服数据微调 |
| Qwen LoRA v4 | Qwen2.5-1.5B-Instruct | 800 train / 200 eval | PEFT LoRA | 100 | Overall score 7.865 | 仍需人工评估模板化风险 |
| v5 planned | Qwen2.5-1.5B-Instruct | 未定 | Real-data augmented LoRA | 100 planned | 规划和探测阶段 | 未下载真实大数据，未训练 |

## Data Evolution

v1 数据为 300 条合成客服 SFT 样本。

v2 数据扩展到 1000 条。

v2 增强了投诉安抚、拒绝不合理请求和售后边界场景。

v3 构造了 100 条统一 evaluation prompts。

v4 将 v2 数据转换为 Qwen messages 格式。

v5 计划引入真实中文电商客服数据。

## Evaluation

项目使用 rule-based rubric 做自动评分。

评分维度包括礼貌、信息询问、规则说明、下一步操作、拒答表达和惩罚项。

它适合做可复现的横向比较。

但它不能等同于人工业务评估。

关键词命中不代表模型真正理解业务规则。

固定话术也可能提升自动分。

## Main Takeaways

MiniMind LoRA 能跑通流程，但效果有限。

更强基座模型非常关键。

Qwen baseline 已超过 MiniMind LoRA v2。

Qwen LoRA v4 在统一自动评分下进一步提升。

真实客服质量仍需要人工评估或 LLM-as-a-judge。

v5 真实数据增强仍处于规划阶段。

## Recommended Reading

- `results_summary.md`
- `notes/interview_notes.md`
- `experiments/final_evaluation_v3_summary.md`
- `experiments/final_qwen_v4_summary.md`
