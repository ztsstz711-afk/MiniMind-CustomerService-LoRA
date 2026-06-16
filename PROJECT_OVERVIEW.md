# Project Overview

## 一句话概览

MiniMind-CustomerService-LoRA 是一个面向“电商售后合规回复”的低资源 SFT / LoRA 微调实验项目。项目从合成客服数据构造开始，先用 MiniMind
跑通 LoRA 微调闭环，再通过系统化评估发现小模型的能力边界，随后迁移到 Qwen2.5-1.5B-Instruct，并验证更强基座模型和 LoRA 对客服合规回复质量的提升。

## 项目主线

项目第一阶段从 300 条电商售后合规 SFT 数据开始，覆盖物流查询、退款进度、退换货申请、发票开具、优惠券使用、商品咨询、订单取消、投诉安抚、拒绝不合理请求和地址修改等 10
类场景。数据先转换为 MiniMind 需要的 `conversations` 格式，再完成 baseline 推理、LoRA 微调、LoRA 推理和 before/after 对比。

MiniMind 阶段证明了低资源 LoRA 链路可以完整跑通：数据构造、格式转换、训练、adapter 保存、推理和评估都能闭环。但评估也暴露出小模型能力边界：虽然 loss
下降，模型开始拟合客服回复风格，但拒答边界、规则解释和稳定性仍然有限。

随后项目进入 v2/v3：数据扩展到 1000 条，重点增强 hard cases 和拒答边界；同时构造 100 条统一 evaluation prompts，并使用 rule-based
rubric 从礼貌安抚、必要信息询问、规则说明、下一步操作、拒答表现、不安全承诺、重复和长度等维度评分。

v4 迁移到 Qwen2.5-1.5B-Instruct。Qwen baseline 已经明显超过 MiniMind LoRA v2；在同一套 v2 数据上训练 Qwen LoRA
后，rule-based overall score 进一步提升到 7.865。这个结果说明更强基座模型对垂直客服场景非常关键，LoRA 可以在已有指令能力基础上进一步强化售后流程和合规表达。

v5 目前只是规划/探测阶段，目标是引入公开中文电商客服真实语料，例如 JDDC / JDDC 2.1 或 CSDS，以增强真实用户表达和客服回复自然度。当前没有下载真实大数据，没有训练
v5 模型。

## Version Comparison

| Version | Base Model | Data Size | Method | Eval Size | Main Result | Limitation |
| --- | --- | ---: | --- | ---: | --- | --- |
| MiniMind baseline | MiniMind full_sft_768 | 0 project fine-tune samples | Baseline inference | 100 | Overall score 5.025 | 未针对电商售后合规场景微调，回复泛化明显 |
| MiniMind LoRA v1 | MiniMind full_sft_768 | 240 train / 60 eval | LoRA | 100 | Overall score 5.375，较 baseline 小幅提升 | 数据仅 300 条，hard cases 和拒答边界不足 |
| MiniMind LoRA v2 | MiniMind full_sft_768 | 800 train / 200 eval | LoRA | 100 | Overall score 5.645，拒绝不合理请求类分数提升 | 小模型能力仍有限，拒答稳定性和自然度不足 |
| Qwen baseline | Qwen2.5-1.5B-Instruct | 0 project fine-tune samples | Baseline inference | 100 | Overall score 6.275，已超过 MiniMind LoRA v2 | 未经过项目客服数据微调，部分流程性表达仍不够稳定 |
| Qwen LoRA v4 | Qwen2.5-1.5B-Instruct | 800 train / 200 eval | PEFT LoRA | 100 | Overall score 7.865，拒绝不合理请求类平均分 8.500，unsafe flags 0 | 存在固定客服话术集中趋势，需要人工评估确认是否模板化 |
| v5 planned | Qwen2.5-1.5B-Instruct | 未定 | Real-data augmented LoRA | 100 planned | 真实数据增强仍在规划/探测阶段 | 未下载真实大数据，未训练，不能声称效果 |

## Evaluation Notes

当前分数来自项目自建的 rule-based evaluation。它适合做粗粒度、可复现的自动对比，但不能等同于人工业务评估。关键词命中会影响得分，例如“您好”“订单号”“规则”“无法”等词
能帮助模型得分，但真实客服质量还需要人工判断：

- 是否真正理解用户诉求。
- 是否解释了正确规则。
- 是否给出了可执行下一步。
- 是否避免过度承诺。
- 是否在违规请求中明确拒绝并给出合规替代方案。
- 是否存在模板化、过拟合或偏题。

因此，本项目的结论应理解为：在同一套自动评分标准下，Qwen LoRA v4 明显优于 MiniMind 与 Qwen baseline；但是否达到真实业务可用，还需要人工评估或
LLM-as-a-judge 进一步验证。

## 当前展示价值

这个项目适合在 GitHub 和实习面试中展示以下能力：

- 面向业务场景设计 SFT 数据格式。
- 将原始 instruction/input/output 数据转换为模型 chat format。
- 跑通 MiniMind 和 Qwen 两条 LoRA 微调链路。
- 保留 baseline，对比微调前后结果。
- 构造统一 evaluation prompts 和 rule-based rubric。
- 如实记录提升、失败案例和局限，而不是只展示 loss 下降。
