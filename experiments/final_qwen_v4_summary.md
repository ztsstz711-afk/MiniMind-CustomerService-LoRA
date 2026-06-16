# Final Qwen v4 Summary

## v4 目标

v4 的目标是把项目从 MiniMind 小模型迁移到更强的 Qwen2.5-1.5B-Instruct 基座模型，并复用同一套 v2 训练数据和 v3 评估集，横向比较：

- MiniMind baseline
- MiniMind LoRA v2
- Qwen2.5-1.5B baseline
- Qwen2.5-1.5B LoRA v4

核心问题不是“loss 是否下降”，而是更强基座模型和 LoRA 微调是否真的改善电商售后合规回复能力。

## Qwen2.5 下载和 Smoke Test

- 模型：Qwen2.5-1.5B-Instruct
- 本地路径：`models/qwen2_5_1_5b_instruct`
- HuggingFace 在线下载曾因网络连接失败，后续改用本地模型目录完成加载
- dtype：bfloat16
- smoke test：成功
- 加载后显存：约 2.875 GB allocated / 2.930 GB reserved
- 生成后显存：约 2.907 GB allocated / 2.936 GB reserved

结论：本机可以稳定加载 Qwen2.5-1.5B-Instruct 并完成生成，不需要降级到 0.5B。

## Qwen Baseline 结果

- 推理集：`data/eval_prompts_v3.jsonl`，100 条
- 输出：`outputs/eval_outputs_qwen_baseline_v4.jsonl`
- 评分：`outputs/eval_scores_qwen_baseline_v4.jsonl`
- 报告：`experiments/eval_report_qwen_baseline_v4.md`
- average score：6.275
- 拒绝不合理请求类平均分：6.600
- unsafe flags：0
- 输出检查：空输出 0，极短 0，重复 0，乱码 0

Qwen baseline 即使没有经过本项目客服数据微调，也已经超过 MiniMind LoRA v2 的 rule-based overall average score。

## Qwen LoRA 训练结果

- 训练数据：`data/qwen_train_v4.jsonl`，800 条
- 验证数据：`data/qwen_eval_v4.jsonl`，200 条
- 模型：Qwen2.5-1.5B-Instruct local
- LoRA adapter：`outputs/qwen2_5_1_5b_lora_v4/adapter_model.safetensors`
- adapter size：36,981,072 bytes，约 35.27 MB
- trainable params：9,232,384
- trainable ratio：0.5945%
- loss：4.038429 -> 0.083962
- loss log 数量：321
- after train memory：3.041 GB allocated / 5.885 GB reserved
- stderr：仅有 `torch_dtype` deprecated 提示
- 无 OOM / NaN / inf / os error 1455

训练链路稳定，adapter 正常保存。但 loss 极低也提示需要警惕过拟合或模板化，必须通过独立 eval prompts 判断业务效果。

## Qwen LoRA Eval 结果

- 推理输出：`outputs/eval_outputs_qwen_lora_v4.jsonl`
- Markdown 输出：`experiments/eval_outputs_qwen_lora_v4.md`
- 评分输出：`outputs/eval_scores_qwen_lora_v4.jsonl`
- 评分报告：`experiments/eval_report_qwen_lora_v4.md`
- average score：7.865
- 拒绝不合理请求类平均分：8.500
- refusal present count：5/10
- unsafe flags：0
- 输出检查：空输出 0，极短 0，重复 0，乱码 0，模板泄漏 0
- 推理显存：after load 2.910 GB allocated / 2.986 GB reserved；after inference 2.941 GB allocated / 2.986 GB reserved

## Category-Level 结果

| category | Qwen baseline | Qwen LoRA v4 | delta |
| --- | ---: | ---: | ---: |
| 优惠券使用 | 6.45 | 7.90 | +1.45 |
| 发票开具 | 6.55 | 7.60 | +1.05 |
| 商品咨询 | 6.30 | 8.00 | +1.70 |
| 地址修改 | 5.15 | 7.85 | +2.70 |
| 投诉安抚 | 5.55 | 8.00 | +2.45 |
| 拒绝不合理请求 | 6.60 | 8.50 | +1.90 |
| 物流查询 | 5.65 | 7.45 | +1.80 |
| 订单取消 | 6.90 | 7.65 | +0.75 |
| 退换货申请 | 6.65 | 8.10 | +1.45 |
| 退款进度 | 6.95 | 7.60 | +0.65 |

## Difficulty-Level 结果

| difficulty | Qwen baseline | Qwen LoRA v4 | delta |
| --- | ---: | ---: | ---: |
| easy | 6.077 | 8.000 | +1.923 |
| medium | 6.211 | 7.803 | +1.592 |
| hard | 6.378 | 7.878 | +1.500 |

## 横向对比

| model | overall average score |
| --- | ---: |
| MiniMind baseline | 5.025 |
| MiniMind LoRA v2 | 5.645 |
| Qwen baseline | 6.275 |
| Qwen LoRA v4 | 7.865 |

## 诚实结论

更强的 Qwen2.5-1.5B 基座模型即使不微调，也明显优于 MiniMind 小模型。完成 LoRA 后，Qwen LoRA v4 在 rule-based rubric 上进一步超过 Qwen baseline，整体分数从 6.275 提升到 7.865，拒绝不合理请求类从 6.600 提升到 8.500。

从自动检查看，Qwen LoRA v4 没有出现空输出、极短输出、严重重复、乱码或训练模板泄漏，unsafe flags 仍为 0。它在投诉安抚、地址修改、拒绝不合理请求、物流查询等类别上提升比较明显。

但也要谨慎解释：部分输出开头明显集中在固定客服话术，例如“您好，先跟您说明一下处理规则...”和“您好，理解您现在比较着急...”。这不一定是坏事，客服场景本身需要稳定话术；但也说明低 loss 可能带来模板化倾向，不能只凭 rule-based 分数判断真实业务质量。

## 局限

- rule-based rubric 只能衡量关键词和粗粒度结构，不能完全代表人工质量。
- 100 条 eval prompts 仍偏小，需要扩展到更多 hard cases。
- LoRA 训练数据是合成数据，表达分布可能偏窄。
- 合规拒答不仅要出现“无法/不能”，还要判断是否给出了正确替代方案，这需要人工或 LLM-as-a-judge 复核。

## 后续可选

- 降低 epochs 或 learning rate 做 ablation，观察是否减少模板化。
- 扩大 eval prompts 到 300~500 条。
- 加入 LLM-as-a-judge，对合规性、事实性、流程完整度分别评分。
- 尝试 Qwen2.5-3B baseline 和 LoRA，对比更强基座模型的上限。
