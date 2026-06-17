# MiniMind-CustomerService-LoRA

电商售后合规回复 LoRA 微调实验。

## TL;DR

This repository records a sequence of small-scale LoRA experiments for Chinese e-commerce
after-sales customer-service responses.

The experiments started with MiniMind to validate the data format, LoRA training loop,
inference scripts, and evaluation pipeline.

Later runs moved to Qwen2.5-1.5B-Instruct after MiniMind results showed clear capacity
limits on policy explanation and refusal behavior.

The project uses synthetic compliance-focused data and a small rule-based evaluation set.

The reported scores are useful for relative comparison inside this repository, but they are
not a substitute for human business evaluation.

实验主线：

```text
low-resource customer-service compliance SFT
-> MiniMind LoRA
-> small-model limitation
-> Qwen2.5-1.5B migration
-> Qwen LoRA improvement
-> rule-based evaluation
```

> 当前分数来自 rule-based evaluation，不能等同于人工业务评估。

## Rule-Based Evaluation Snapshot

![Model score comparison](assets/model_score_comparison.png)

| Model | Overall Score |
| --- | ---: |
| MiniMind baseline | 5.025 |
| MiniMind LoRA v1 | 5.375 |
| MiniMind LoRA v2 | 5.645 |
| Qwen baseline | 6.275 |
| Qwen LoRA v4 | 7.865 |

Scores are produced by a simple rule-based rubric and are mainly used for relative comparison
within this repository.

## Main Artifacts

- [Project overview](PROJECT_OVERVIEW.md)
- [Results summary](results_summary.md)
- [Qwen v4 final summary](experiments/final_qwen_v4_summary.md)
- [v3 evaluation summary](experiments/final_evaluation_v3_summary.md)

## Project Motivation

电商售后回复是一个适合做低资源微调实验的场景。

它有明确业务规则。

它要求模型不仅会回答，还要礼貌安抚、解释规则、询问必要信息、给出下一步操作。

它还要求模型不能乱承诺，不能绕过平台规则，不能泄露隐私。

因此这个场景非常适合观察 SFT / LoRA 是否能改善回复风格和合规边界。

## Scope

本项目覆盖以下售后场景：

- 物流查询
- 退款进度
- 退换货申请
- 发票开具
- 优惠券使用
- 商品咨询
- 订单取消
- 投诉安抚
- 拒绝不合理请求
- 地址修改

## Data

v1 数据：

- 原始数据：`data/customer_service_sft.jsonl`
- 总量：300
- train：240
- eval：60
- 字段：`instruction`、`input`、`output`、`category`

v2 数据：

- 原始数据：`data/customer_service_sft_v2.jsonl`
- 总量：1000
- train：800
- eval：200
- 新增字段：`difficulty`、`tags`
- 重点增强 hard cases 和拒答边界

v3 评估集：

- 文件：`data/eval_prompts_v3.jsonl`
- 数量：100
- 每类 10 条
- 用于 MiniMind 和 Qwen 的统一自动评分

v4 Qwen 数据：

- `data/qwen_train_v4.jsonl`
- `data/qwen_eval_v4.jsonl`
- 格式为 Qwen messages SFT 格式

## Model Tracks

### MiniMind Track

MiniMind 线用于低成本跑通完整 LoRA 微调流程。

它包括：

- MiniMind baseline 推理
- MiniMind LoRA v1 训练
- MiniMind LoRA v2 训练
- baseline / LoRA v1 / LoRA v2 对比

主要结论：

- MiniMind LoRA 有提升。
- MiniMind LoRA v2 从 5.025 提升到 5.645。
- 但小模型能力限制明显。
- 复杂规则、拒答边界和自然表达仍不稳定。

### Qwen Track

Qwen 线用于验证更强基座模型的价值。

它包括：

- Qwen2.5-1.5B-Instruct baseline
- Qwen LoRA smoke training
- Qwen LoRA v4 full training
- Qwen baseline vs Qwen LoRA v4 对比

主要结论：

- Qwen baseline overall score 为 6.275。
- Qwen baseline 已超过 MiniMind LoRA v2。
- Qwen LoRA v4 overall score 为 7.865。
- Qwen LoRA v4 拒绝不合理请求类平均分为 8.500。
- Qwen LoRA v4 unsafe flags 为 0。

## Evaluation

本项目使用 rule-based rubric 做自动评估。

评分维度包括：

- 礼貌安抚
- 必要信息询问
- 规则说明
- 下一步操作
- 拒答表达
- 不安全承诺惩罚
- 重复惩罚
- 长度惩罚

这个评估方式可复现、成本低，适合横向比较。

但它不能替代人工业务评估。

关键词命中不等于真正理解业务规则。

固定客服话术也可能获得较高分。

因此所有分数都应理解为离线粗评结果。

## Key Results

| Version | Base Model | Method | Eval Size | Result |
| --- | --- | --- | ---: | --- |
| MiniMind baseline | MiniMind full_sft_768 | Baseline | 100 | 5.025 |
| MiniMind LoRA v1 | MiniMind full_sft_768 | LoRA | 100 | 5.375 |
| MiniMind LoRA v2 | MiniMind full_sft_768 | LoRA | 100 | 5.645 |
| Qwen baseline | Qwen2.5-1.5B-Instruct | Baseline | 100 | 6.275 |
| Qwen LoRA v4 | Qwen2.5-1.5B-Instruct | PEFT LoRA | 100 | 7.865 |

## Important Findings

MiniMind LoRA 证明了低资源 LoRA 流程可行。

MiniMind LoRA v2 有提升，但提升幅度有限。

Qwen baseline 已经强于 MiniMind LoRA v2。

Qwen LoRA v4 在 rule-based evaluation 下进一步提升。

训练 loss 下降不等于线上可用。

自动评分提升也不等于真实客服质量完全达标。

## Future Work: Real-data Extension

后续计划探索真实中文电商客服语料，用于增强用户表达多样性和客服回复自然度。

候选数据源包括：

- JDDC
- JDDC 2.1
- CSDS

当前状态：

- 只做了数据源规划和探测。
- 没有下载真实大数据。
- 没有基于真实数据继续训练。
- 没有把真实原始数据提交到 GitHub。

这些数据源目前只是后续扩展方向。

## Repository Hygiene

以下目录不提交到 GitHub：

- `outputs/`
- `models/`
- `minimind/`
- `data/raw_real_v5/`
- `checkpoints/`

以下文件类型不提交：

- `*.pt`
- `*.pth`
- `*.bin`
- `*.safetensors`

## Repository Structure

主要公开文档：

1. `PROJECT_OVERVIEW.md`
2. `results_summary.md`
3. `assets/model_score_comparison.png`
4. `experiments/final_evaluation_v3_summary.md`
5. `experiments/final_qwen_v4_summary.md`

## Reproducibility Notes

本仓库保留数据构造脚本、格式转换脚本、训练 wrapper、推理脚本和评估脚本。

但是模型权重、本地输出和上游 MiniMind 仓库不提交。

如果要复现实验，需要自行准备对应 checkpoint 和本地模型。

## Limitations

数据主要是合成数据。

评估集只有 100 条。

rule-based evaluation 不能替代人工业务评估。

当前主要是单轮客服回复实验，不包含完整多轮服务流程。

真实数据增强仍在规划阶段。

## Suggested Next Steps

引入真实客服文本数据。

保留合成 hard cases。

加入人工评分或 LLM-as-a-judge。

扩展 evaluation prompts。

尝试 Qwen2.5-3B baseline 和 LoRA。
