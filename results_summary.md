# Results Summary

## Source Files

MiniMind v3 evaluation:

- `experiments/eval_report_baseline_v3.md`
- `experiments/eval_report_lora_v1_v3.md`
- `experiments/eval_report_lora_v2_v3.md`
- `experiments/eval_score_comparison_v3.md`
- `experiments/final_evaluation_v3_summary.md`

Qwen v4 evaluation:

- `experiments/eval_report_qwen_baseline_v4.md`
- `experiments/eval_report_qwen_lora_v4.md`
- `experiments/qwen_baseline_lora_comparison_v4.md`
- `experiments/final_qwen_v4_summary.md`

## Overall Scores

| Model | Overall Score | Notes |
| --- | ---: | --- |
| MiniMind baseline | 5.025 | 未使用项目数据微调 |
| MiniMind LoRA v1 | 5.375 | 300 条合成数据 |
| MiniMind LoRA v2 | 5.645 | 1000 条合成数据，增强 hard cases |
| Qwen baseline | 6.275 | Qwen2.5-1.5B-Instruct baseline |
| Qwen LoRA v4 | 7.865 | Qwen2.5-1.5B-Instruct + LoRA |

## MiniMind Results

MiniMind baseline 的 overall score 为 5.025。

MiniMind LoRA v1 的 overall score 为 5.375。

MiniMind LoRA v2 的 overall score 为 5.645。

MiniMind LoRA v2 相比 baseline 提升 0.620。

这个提升说明 LoRA 学到了一部分电商售后客服风格。

但提升幅度有限。

主要限制来自小模型能力、合成数据规模和拒答边界难度。

## Qwen Results

Qwen baseline 的 overall score 为 6.275。

Qwen LoRA v4 的 overall score 为 7.865。

Qwen LoRA v4 相比 Qwen baseline 提升 1.590。

Qwen baseline 已超过 MiniMind LoRA v2。

这说明更强基座模型非常关键。

Qwen LoRA v4 进一步提升，说明垂直售后合规数据对 Qwen 仍然有效。

## Refusal Category

Qwen baseline 拒绝不合理请求类平均分为 6.600。

Qwen LoRA v4 拒绝不合理请求类平均分为 8.500。

Qwen LoRA v4 unsafe flags 为 0。

这说明 Qwen LoRA v4 在 rule-based rubric 下更常命中拒答相关表达。

但这不等于真实业务拒答完全可靠。

拒答质量仍需人工检查。

## Cross-Model Comparison

| Comparison | Result |
| --- | --- |
| MiniMind LoRA v2 vs MiniMind baseline | 有提升，但幅度有限 |
| Qwen baseline vs MiniMind LoRA v2 | Qwen baseline 更强 |
| Qwen LoRA v4 vs Qwen baseline | 明显提升 |
| Qwen LoRA v4 vs MiniMind LoRA v2 | Qwen LoRA v4 明显更优 |

## Evaluation Limitation

当前分数来自 rule-based rubric。

它基于关键词和简单规则。

它可以快速、可复现地比较模型。

但它不能替代人工业务评估。

关键词命中不代表真实理解。

固定客服话术可能提高自动分。

规则解释是否正确仍需人工判断。

拒答是否合规也需要人工或 LLM-as-a-judge 复核。

## Bottom Line

MiniMind 阶段证明了低资源 LoRA 链路可行。

Qwen 阶段证明了更强基座模型和 LoRA 的明显优势。

Qwen LoRA v4 是当前项目内自动评分最高的版本。

但项目仍然是离线实验。

它不能直接宣称达到线上客服系统效果。
