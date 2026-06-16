# Qwen Baseline v4 Summary

## Smoke Test 成功结果

Qwen2.5-1.5B-Instruct 已通过本地 smoke test：

- 本地路径：`models/qwen2_5_1_5b_instruct`
- dtype：bfloat16
- CUDA memory after load：2.875 GB allocated / 2.930 GB reserved
- CUDA memory after generation：2.907 GB allocated / 2.936 GB reserved
- 结果：成功生成电商售后客服回复
- 是否需要降级到 0.5B：不需要

## Qwen Baseline 100 条推理结果

使用同一套 v3 eval prompts：

- 输入：`data/eval_prompts_v3.jsonl`
- 输出 JSONL：`outputs/eval_outputs_qwen_baseline_v4.jsonl`
- 输出 Markdown：`experiments/eval_outputs_qwen_baseline_v4.md`
- 模型：`models/qwen2_5_1_5b_instruct`
- model_name：`qwen2_5_1_5b_baseline`
- 推理条数：100
- dtype：bfloat16
- max_new_tokens：160
- temperature：0.7
- top_p：0.9

显存：

- before load：0.000 GB allocated / 0.000 GB reserved
- after load：2.875 GB allocated / 2.930 GB reserved
- after inference：2.907 GB allocated / 2.938 GB reserved

## 输出质量检查结果

检查脚本：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_qwen_baseline_v4_outputs.py
```

结果：

- 输出条数：100
- 空输出：0
- 极短输出：0
- 重复输出：0
- 疑似乱码：0
- 检查状态：通过

相比 MiniMind baseline / LoRA v1 / LoRA v2，Qwen baseline 的输出结构稳定性明显更好，至少在该 100 条评估上没有出现空输出、明显重复或替换字符乱码。

## 自动评分结果

评分脚本：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/evaluate_outputs_v3.py --model_name qwen2_5_1_5b_baseline --input_path outputs/eval_outputs_qwen_baseline_v4.jsonl --eval_path data/eval_prompts_v3.jsonl --output_scores_path outputs/eval_scores_qwen_baseline_v4.jsonl --report_path experiments/eval_report_qwen_baseline_v4.md
```

结果：

- overall average score：6.275
- refusal category average score：6.600
- refusal present count：1/10
- unsafe flags count：0

类别平均分：

| category | score |
| --- | ---: |
| 优惠券使用 | 6.450 |
| 发票开具 | 6.550 |
| 商品咨询 | 6.300 |
| 地址修改 | 5.150 |
| 投诉安抚 | 5.550 |
| 拒绝不合理请求 | 6.600 |
| 物流查询 | 5.650 |
| 订单取消 | 6.900 |
| 退换货申请 | 6.650 |
| 退款进度 | 6.950 |

## 与 MiniMind baseline / LoRA v2 的初步对比

| model | overall avg | refusal avg | unsafe flags |
| --- | ---: | ---: | ---: |
| MiniMind baseline | 5.025 | 6.350 | 0 |
| MiniMind LoRA v2 | 5.645 | 7.450 | 0 |
| Qwen2.5-1.5B baseline | 6.275 | 6.600 | 0 |

Qwen baseline 在 overall average score 上已经超过 MiniMind LoRA v2：

- Qwen baseline：6.275
- MiniMind LoRA v2：5.645

这说明更强的指令基座模型即使不经过本项目客服数据微调，也能在礼貌性、通用流程表达和语言稳定性上取得更好的 rule-based 总分。

## 重点观察

### 是否更像客服

是。Qwen baseline 的输出更自然，格式更完整，基本能保持客服语气。它没有出现 MiniMind 常见的明显重复、乱码和大段偏题模板化输出。

### 拒绝不合理请求是否更稳

还不能说稳定。虽然拒绝不合理请求类别平均分为 6.600，高于 MiniMind baseline，但低于 MiniMind LoRA v2 的 7.450，并且 `refusal_present` 只有 1/10。

这说明 Qwen baseline 更会“说客服话”，但未经客服拒答边界 LoRA 时，不一定会稳定明确拒绝违规请求。

### 是否还有过度承诺或不合规问题

rule-based unsafe flags 为 0，但这不代表完全合规。自动规则只检查有限关键词，仍需要人工检查是否存在隐含承诺、流程不准确或拒答不明确。

## 局限

- rule-based 评分粗糙，关键词命中不能完全代表真实业务质量。
- Qwen baseline 尚未经过本项目客服数据 LoRA。
- 拒绝不合理请求仍需重点人工评估。
- 后续需要 Qwen LoRA 训练后再与 MiniMind LoRA v2 做公平对比。

## 下一步

- 进行 Qwen LoRA 训练。
- 使用同一套 `data/eval_prompts_v3.jsonl` 做 Qwen LoRA 100 条推理。
- 复用 `scripts/evaluate_outputs_v3.py` 自动评分。
- 生成 MiniMind LoRA v2 vs Qwen baseline vs Qwen LoRA 的横向对比。
