# Results Summary

## 结果来源文件

MiniMind v3 评估：

- `experiments/eval_report_baseline_v3.md`
- `experiments/eval_report_lora_v1_v3.md`
- `experiments/eval_report_lora_v2_v3.md`
- `experiments/eval_score_comparison_v3.md`
- `experiments/final_evaluation_v3_summary.md`

Qwen v4 评估：

- `experiments/eval_report_qwen_baseline_v4.md`
- `experiments/eval_report_qwen_lora_v4.md`
- `experiments/qwen_baseline_lora_comparison_v4.md`
- `experiments/final_qwen_v4_summary.md`

## Overall Score

| Model | Overall Score | Notes |
| --- | ---: | --- |
| MiniMind baseline | 5.025 | 未使用项目数据微调 |
| MiniMind LoRA v1 | 5.375 | 300 条合成数据，240 train / 60 eval |
| MiniMind LoRA v2 | 5.645 | 1000 条合成数据，800 train / 200 eval，增强 hard cases |
| Qwen baseline | 6.275 | Qwen2.5-1.5B-Instruct 未经项目数据微调 |
| Qwen LoRA v4 | 7.865 | Qwen2.5-1.5B-Instruct + 800 条项目客服数据 LoRA |

## Qwen LoRA v4 相比 Qwen Baseline

Qwen LoRA v4 在同一套 100 条 `eval_prompts_v3` 上，相比 Qwen baseline 有明显提升：

- Qwen baseline overall score：6.275
- Qwen LoRA v4 overall score：7.865
- 提升：+1.590
- Qwen baseline 拒绝不合理请求类平均分：6.600
- Qwen LoRA v4 拒绝不合理请求类平均分：8.500
- Qwen LoRA v4 unsafe flags：0
- Qwen LoRA v4 输出检查：空输出 0，极短 0，重复 0，乱码 0，模板泄漏 0

这个结果说明，在 Qwen2.5-1.5B-Instruct 已有通用指令能力的基础上，少量垂直售后合规数据的 LoRA 微调能进一步强化客服流程、规则表达和拒答边界。

## MiniMind LoRA v2 的结论

MiniMind LoRA v2 相比 MiniMind baseline 有提升：

- MiniMind baseline：5.025
- MiniMind LoRA v2：5.645
- 提升：+0.620

但 MiniMind LoRA v2 仍受小模型能力限制。即使 v2 数据扩展到 1000 条并增强 hard cases，模型在真实客服自然度、复杂规则解释、拒答稳定性和偏题控制上仍然有限。
这个阶段的价值主要是跑通低资源 LoRA 全流程，并暴露小模型和小数据的边界。

## 横向结论

| Comparison | Result |
| --- | --- |
| MiniMind LoRA v2 vs MiniMind baseline | 有提升，但幅度有限 |
| Qwen baseline vs MiniMind LoRA v2 | Qwen baseline 更强，说明基座模型能力非常关键 |
| Qwen LoRA v4 vs Qwen baseline | 明显提升，说明垂直 LoRA 对客服合规风格有效 |
| Qwen LoRA v4 vs MiniMind LoRA v2 | Qwen LoRA v4 明显更优 |

## 自动评分局限

当前 evaluation 是 rule-based rubric，不是人工业务评估。它通过关键词和简单规则判断礼貌安抚、必要信息、规则说明、下一步操作、拒答、不安全承诺、重复和长度等维度。

局限包括：

- 关键词命中不等于真正理解业务规则。
- 模型可能因为固定客服话术而获得更高分。
- 拒答质量不只看是否出现“无法/不能”，还要看是否提供合规替代方案。
- 自动评分不能完全识别事实错误、隐含承诺、上下文误解或语气问题。
- 真实业务效果仍需要人工评估或 LLM-as-a-judge 复核。

因此，本项目的分数只能作为同一评估标准下的可复现粗评，不能直接宣称模型已达到工业级客服系统效果。
