# Qwen LoRA Smoke v4

## Smoke Test 目标

先用极小样本跑通 Qwen2.5 + PEFT LoRA 的训练链路，确认：

- 模型能进入训练模式
- LoRA adapter 能挂载
- loss 能正常计算
- 显存不会 OOM
- adapter 能保存
- 只保存 LoRA adapter，不保存完整模型

## 数据

- 输入完整数据：`data/qwen_train_v4.jsonl`
- smoke 数据：`data/qwen_train_smoke_v4.jsonl`
- 使用数据量：20 条

## 模型

- Qwen2.5-1.5B-Instruct local
- 本地路径：`models/qwen2_5_1_5b_instruct`
- dtype：bfloat16
- device：cuda
- 不使用 bitsandbytes
- 不使用 4bit QLoRA

## 训练配置

- LoRA r：8
- LoRA alpha：16
- LoRA dropout：0.05
- target modules：`q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`
- num_train_epochs：1
- per_device_train_batch_size：1
- gradient_accumulation_steps：4
- learning_rate：2e-4
- max_seq_length：512
- logging_steps：1
- save：仅最终保存 adapter
- output_dir：`outputs/qwen_lora_smoke_v4`

## 待填写

## 运行结果

- 是否成功：成功
- smoke 数据：`data/qwen_train_smoke_v4.jsonl`
- smoke 数据条数：20
- stdout：`outputs/qwen_lora_smoke_v4/train_stdout.txt`
- stderr：`outputs/qwen_lora_smoke_v4/train_stderr.txt`
- stderr：空，无报错

## Loss

- loss logs：20
- first loss：3.978802，step 1
- last loss：3.096197，step 20
- optimizer steps：5
- NaN / inf：未发现

## Adapter

- adapter config：`outputs/qwen_lora_smoke_v4/adapter_config.json`
- adapter weights：`outputs/qwen_lora_smoke_v4/adapter_model.safetensors`
- adapter size：36,981,072 bytes，约 35.27 MB
- 保存方式：仅保存 LoRA adapter，未保存完整模型

## 显存占用

- before load：0.000 GB allocated / 0.000 GB reserved
- after load：2.875 GB allocated / 2.932 GB reserved
- after train：3.090 GB allocated / 5.355 GB reserved

## 训练参数确认

- trainable params：9,232,384
- all params：1,552,946,688
- trainable ratio：0.5945%
- dtype：bfloat16
- device：cuda
- batch_size：1
- gradient_accumulation_steps：4
- learning_rate：2e-4
- max_seq_length：512
- LoRA r：8
- LoRA alpha：16
- LoRA dropout：0.05

## 结论

Qwen2.5-1.5B + PEFT LoRA smoke training 链路已跑通：

- 模型可以进入训练模式
- LoRA adapter 成功挂载
- loss 可以正常计算
- 显存没有 OOM
- adapter 可以保存
- 未保存完整模型

建议进入完整 Qwen LoRA 训练，但仍应沿用保守配置，并继续监控显存、loss、adapter 保存和输出质量。
