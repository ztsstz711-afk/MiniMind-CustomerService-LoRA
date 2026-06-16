# Qwen Baseline vs Qwen LoRA v4 Comparison

## Overall

| model | overall_avg | refusal_avg | unsafe_flags | repetition_penalty | length_penalty |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen baseline | 6.275 | 6.6 | 0 | 0 | 0 |
| Qwen LoRA v4 | 7.865 | 8.5 | 0 | 0 | 0 |

- overall delta (LoRA - baseline): 1.59
- 判断：如果 LoRA 分数下降或重复惩罚增加，说明极低训练 loss 可能对应过拟合、模板化或训练数据分布过窄，而不一定代表业务质量提升。

## Category Average

| category | baseline | qwen_lora_v4 | delta |
| --- | ---: | ---: | ---: |
| 优惠券使用 | 6.45 | 7.9 | 1.45 |
| 发票开具 | 6.55 | 7.6 | 1.05 |
| 商品咨询 | 6.3 | 8.0 | 1.7 |
| 地址修改 | 5.15 | 7.85 | 2.7 |
| 投诉安抚 | 5.55 | 8.0 | 2.45 |
| 拒绝不合理请求 | 6.6 | 8.5 | 1.9 |
| 物流查询 | 5.65 | 7.45 | 1.8 |
| 订单取消 | 6.9 | 7.65 | 0.75 |
| 退换货申请 | 6.65 | 8.1 | 1.45 |
| 退款进度 | 6.95 | 7.6 | 0.65 |

## Difficulty Average

| difficulty | baseline | qwen_lora_v4 | delta |
| --- | ---: | ---: | ---: |
| easy | 6.077 | 8.0 | 1.923 |
| hard | 6.378 | 7.878 | 1.5 |
| medium | 6.211 | 7.803 | 1.592 |

## Key Notes

- 本报告使用 rule-based rubric，只能作为粗粒度自动评估。
- 需要结合人工阅读判断：LoRA 是否更合规，是否更像售后客服，是否出现模板化和过拟合。
- 下一步可扩展到 LLM-as-a-judge 或人工 rubrics 复评。