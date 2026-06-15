# LoRA Training Log

## 训练目标

使用 MiniMind 原生 LoRA 流程，让模型在电商售后合规回复场景中更稳定地进行礼貌安抚、规则解释、必要信息核实、下一步操作说明，并能拒绝违规请求。

## 训练状态

- 状态：成功完成
- 训练脚本：`scripts/run_lora_training.py`
- 上游脚本：`minimind/trainer/train_lora.py`
- stdout：`outputs/lora_train_stdout.txt`
- stderr：`outputs/lora_train_stderr.txt`
- 输出检查脚本：`scripts/check_lora_training_outputs.py`
- 输出检查结果：通过

## 数据集

- 训练集：`data/minimind_train.jsonl`
- 样本数：240
- 评估集：`data/minimind_eval.jsonl`
- 样本数：60
- 格式：MiniMind `conversations` JSONL

## Base Checkpoint

- 路径：`minimind/out/full_sft_768.pth`
- tokenizer：`minimind/model/`
- 模型：Dense MiniMind，`hidden_size=768`，`num_hidden_layers=8`

## 训练参数

- `lora_name`: `lora_customer_service`
- `batch_size`: 4
- `accumulation_steps`: 4
- `effective_batch_size`: 16
- `epochs`: 3
- `learning_rate`: 1e-4
- `max_seq_len`: 340
- `device`: `cuda:0`
- `dtype`: `bfloat16`
- `num_workers`: 0
- `save_interval`: 100
- `log_interval`: 5
- `wandb/swanlab`: disabled

## Loss 变化

stdout 中共记录 36 条 loss 日志。

| 位置 | epoch/step | loss |
| --- | --- | ---: |
| 起始 | `1/3`, `5/60` | 3.7383 |
| 末尾 | `3/3`, `60/60` | 2.8888 |

loss 整体有下降，未发现 NaN 或 inf。

## 耗时

日志中的 `epoch_time` 均显示为 `0.0min`，说明本次小数据 LoRA 训练耗时很短；stdout/stderr 文件时间戳显示训练在 2026-06-16 04:41 左右完成。

## 显存

训练日志未记录显存峰值。训练过程未出现 CUDA OOM。

## 输出文件列表

LoRA 输出目录：

```text
outputs/lora_customer_service/
```

文件：

| 文件 | 大小 |
| --- | ---: |
| `lora_customer_service_768.pth` | 798,063 bytes（约 0.76 MB） |

## Warning / Error 检查

- stdout：有正常 loss 日志；未发现 `NaN`、`inf`、`Error`、`Traceback`、`CUDA out of memory`、checkpoint mismatch 或 dtype/bfloat16 报错。
- stderr：仅包含 datasets 生成 train split 的进度信息；未发现错误。
- stdout 中中文参数统计行存在终端编码显示异常，但不影响训练结果和 checkpoint 保存。

## 下一步计划

1. 创建 LoRA 推理脚本，加载 `full_sft_768.pth` + `outputs/lora_customer_service/lora_customer_service_768.pth`。
2. 使用 `data/baseline_prompts.jsonl` 生成 LoRA 输出。
3. 保存 `experiments/lora_outputs.md` 和 `outputs/lora_outputs.jsonl`。
4. 与 `experiments/baseline_outputs.md` 做 before/after 对比，重点观察礼貌安抚、规则解释、必要信息、下一步操作和违规拒答边界。
