# Eval Score Comparison v3

Rule-based rubric can only provide coarse automatic evaluation. It does not fully represent real business quality, factual correctness, or compliance reliability.

## Overall Average Score

| model | overall_avg | unsafe_flags | refusal_avg | refusal_present | repetition_penalty | length_penalty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 5.025 | 0 | 6.35 | 3/10 | 2.0 | 0.0 |
| lora_v1 | 5.375 | 0 | 6.85 | 5/10 | 8.0 | 0.0 |
| lora_v2 | 5.645 | 0 | 7.45 | 3/10 | 6.0 | 0.0 |

## Category Average Score

| category | baseline | lora_v1 | lora_v2 | best_model |
| --- | ---: | ---: | ---: | --- |
| 优惠券使用 | 4.45 | 5.05 | 6.55 | lora_v2 |
| 发票开具 | 4.65 | 4.95 | 4.9 | lora_v1 |
| 商品咨询 | 3.75 | 3.45 | 3.5 | baseline |
| 地址修改 | 5.05 | 5.8 | 4.55 | lora_v1 |
| 投诉安抚 | 4.7 | 5.75 | 6.15 | lora_v2 |
| 拒绝不合理请求 | 6.35 | 6.85 | 7.45 | lora_v2 |
| 物流查询 | 5.3 | 5.2 | 5.1 | baseline |
| 订单取消 | 5.2 | 5.25 | 5.7 | lora_v2 |
| 退换货申请 | 4.2 | 5.9 | 6.2 | lora_v2 |
| 退款进度 | 6.6 | 5.55 | 6.35 | baseline |

## Difficulty Average Score

| difficulty | baseline | lora_v1 | lora_v2 |
| --- | ---: | ---: | ---: |
| easy | 5.077 | 4.538 | 4.5 |
| hard | 5.51 | 6.01 | 6.347 |
| medium | 4.382 | 4.842 | 5.132 |

## Delta Summary

- LoRA v1 vs baseline overall delta: 0.35
- LoRA v2 vs LoRA v1 overall delta: 0.27
- LoRA v2 vs baseline overall delta: 0.62

## Important Reminder

This rubric is intentionally simple and keyword-driven. It is useful for trend screening, but it cannot replace manual review or LLM-as-a-judge evaluation for nuanced customer-service quality.