# Eval Inference v3 Log

## 评估集

- eval prompts：`data/eval_prompts_v3.jsonl`
- 数量：100
- 类别：10 类，每类 10 条
- difficulty 分布：easy 13 / medium 38 / hard 49

## 三个模型计划

1. baseline
   - base checkpoint：`minimind/out/full_sft_768.pth`
   - LoRA：不加载
   - 输出：`outputs/eval_outputs_baseline_v3.jsonl`
   - Markdown：`experiments/eval_outputs_baseline_v3.md`

2. LoRA v1
   - base checkpoint：`minimind/out/full_sft_768.pth`
   - LoRA checkpoint：`outputs/lora_customer_service/lora_customer_service_768.pth`
   - 输出：`outputs/eval_outputs_lora_v1_v3.jsonl`
   - Markdown：`experiments/eval_outputs_lora_v1_v3.md`
   - 状态：已完成

3. LoRA v2
   - base checkpoint：`minimind/out/full_sft_768.pth`
   - LoRA checkpoint：`outputs/lora_customer_service_v2/lora_customer_service_v2_768.pth`
   - 输出：`outputs/eval_outputs_lora_v2_v3.jsonl`
   - Markdown：`experiments/eval_outputs_lora_v2_v3.md`
   - 状态：已完成

## Baseline 推理配置

- hidden_size：768
- num_hidden_layers：8
- use_moe：0
- max_new_tokens：220
- temperature：0.7
- top_p：0.9
- device：cuda

## Baseline 检查结果

- 状态：已完成
- 输出 JSONL：`outputs/eval_outputs_baseline_v3.jsonl`
- 输出 Markdown：`experiments/eval_outputs_baseline_v3.md`
- 输出条数：100
- 空输出：0
- 极短输出：0
- 明显重复输出行数：2
- 明显重复输出行号：35, 52
- 完全重复输出组：0
- 完全重复输出行数：0
- 疑似乱码输出行数：2
- 疑似乱码输出行号：26, 98

检查脚本已通过：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_eval_inference_v3_outputs.py --model_name baseline
```

说明：疑似乱码为模型生成文本中出现 `�` 替换字符，属于 baseline 生成质量问题，不是 JSONL 结构或文件写入错误。

## 下一步

- 使用 `scripts/evaluate_outputs_v3.py` 对 baseline / LoRA v1 / LoRA v2 统一评分。

## LoRA v1 检查结果

- 状态：已完成
- 输出 JSONL：`outputs/eval_outputs_lora_v1_v3.jsonl`
- 输出 Markdown：`experiments/eval_outputs_lora_v1_v3.md`
- 输出条数：100
- 空输出：0
- 极短输出：0
- 明显重复输出行数：8
- 明显重复输出行号：31, 50, 64, 67, 79, 85, 88, 97
- 完全重复输出组：0
- 完全重复输出行数：0
- 疑似乱码输出行数：1
- 疑似乱码输出行号：32

检查脚本已通过：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_eval_inference_v3_outputs.py --model_name lora_v1
```

## LoRA v2 检查结果

- 状态：已完成
- 输出 JSONL：`outputs/eval_outputs_lora_v2_v3.jsonl`
- 输出 Markdown：`experiments/eval_outputs_lora_v2_v3.md`
- 输出条数：100
- 空输出：0
- 极短输出：0
- 明显重复输出行数：6
- 明显重复输出行号：17, 32, 51, 52, 62, 67
- 完全重复输出组：0
- 完全重复输出行数：0
- 疑似乱码输出行数：1
- 疑似乱码输出行号：71

检查脚本已通过：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_eval_inference_v3_outputs.py --model_name lora_v2
```

## 三模型输出汇总

| model | rows | empty | very_short | repeated_rows | garbled_rows | check |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 100 | 0 | 0 | 2 | 2 | passed |
| lora_v1 | 100 | 0 | 0 | 8 | 1 | passed |
| lora_v2 | 100 | 0 | 0 | 6 | 1 | passed |

三个模型的 100 条 v3 eval 输出都已准备好。下一步是运行 rule-based rubric 自动评分。
