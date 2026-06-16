# Qwen LoRA v4 Training Log

## 训练目标

使用完整 `data/qwen_train_v4.jsonl` 的 800 条电商售后数据训练 Qwen2.5-1.5B LoRA adapter。只保存 LoRA adapter，不保存完整模型。

## 模型

- Qwen2.5-1.5B-Instruct local
- 本地路径：`models/qwen2_5_1_5b_instruct`
- dtype：bfloat16
- device：cuda
- 不使用 bitsandbytes
- 不使用 4bit QLoRA

## 数据

- train：`data/qwen_train_v4.jsonl`，800 条
- eval：`data/qwen_eval_v4.jsonl`，200 条

## 训练参数

- num_train_epochs：2
- per_device_train_batch_size：1
- gradient_accumulation_steps：8
- learning_rate：2e-4
- max_seq_length：512
- logging_steps：5
- warmup_ratio：0.03
- weight_decay：0.0
- max_grad_norm：1.0
- save：仅最终保存 adapter
- output_dir：`outputs/qwen2_5_1_5b_lora_v4`

## LoRA 参数

- r：8
- lora_alpha：16
- lora_dropout：0.05
- target_modules：`q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`

## Smoke Training 回顾

- smoke samples：20
- loss：3.978802 -> 3.096197
- adapter：`outputs/qwen_lora_smoke_v4/adapter_model.safetensors`
- adapter size：约 35.27 MB
- trainable params：9,232,384
- trainable ratio：0.5945%
- after train memory：3.090 GB allocated / 5.355 GB reserved
- 无 OOM、无 NaN/inf、无 os error 1455

## 训练结果

- 训练是否成功：成功
- 训练数据：800 train / 200 eval
- forward steps：1600
- optimizer steps：200
- loss log 数量：321
- first loss：4.038429，step 1
- last loss：0.083962，step 1600
- adapter：`outputs/qwen2_5_1_5b_lora_v4/adapter_model.safetensors`
- adapter size：36,981,072 bytes，约 35.27 MB
- adapter config：`outputs/qwen2_5_1_5b_lora_v4/adapter_config.json`
- stdout：`outputs/qwen_lora_v4_train_stdout.txt`
- stderr：`outputs/qwen_lora_v4_train_stderr.txt`
- 显存 after train：3.041 GB allocated / 5.885 GB reserved
- stderr 检查：仅有 `torch_dtype` deprecated 提示，无训练错误
- 是否有 OOM / NaN / inf / os error 1455：无
- 输出检查脚本：`scripts/check_qwen_lora_v4_outputs.py` 已通过
- 是否可以进入 Qwen LoRA 100 条 eval 推理：可以

## 下一步

使用 `data/eval_prompts_v3.jsonl` 对 Qwen LoRA v4 adapter 做 100 条 eval 推理，并与 Qwen baseline、MiniMind LoRA v2 做统一 rule-based rubric 对比。注意不能只凭训练 loss 判断业务效果，仍需要看拒答边界、规则解释和投诉安抚等类别表现。
