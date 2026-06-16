# LoRA Training v2 Log

## v2 训练目标

基于 v2 电商售后合规数据重新训练 MiniMind LoRA，让模型在以下场景中更稳定：

- 礼貌安抚
- 规则解释
- 询问订单号或必要信息
- 给出下一步操作
- 礼貌拒绝违规或不合理请求
- 减少泛化、偏题和无边界承诺

v2 LoRA 训练已完成，并通过输出检查脚本验证。

## v2 数据规模

- 原始数据：`data/customer_service_sft_v2.jsonl`，1000 条
- MiniMind train：`data/minimind_train_v2.jsonl`，800 条
- MiniMind eval：`data/minimind_eval_v2.jsonl`，200 条
- hard samples：557 条
- 重点增强：拒答边界、投诉安抚、退款/退货/发票/优惠券边界样本

## 相比 v1 的区别

- v1 数据：300 条，train/eval 为 240/60
- v2 数据：1000 条，train/eval 为 800/200
- v2 新增 `difficulty` 和 `tags`
- v2 hard cases 明显增加，尤其是拒绝不合理请求和投诉安抚
- v2 训练输出不会覆盖 v1 adapter

## 训练配置

- base checkpoint：`minimind/out/full_sft_768.pth`
- data_path：`data/minimind_train_v2.jsonl`
- output_dir：`outputs/lora_customer_service_v2/`
- lora_name：`lora_customer_service_v2`
- batch_size：4
- accumulation_steps：4
- effective batch size：16
- epochs：3
- learning_rate：1e-4
- max_seq_len：340
- device：cuda:0
- dtype：bfloat16
- num_workers：0
- log_interval：10
- save_interval：200
- hidden_size：768
- num_hidden_layers：8
- use_moe：0
- from_weight：full_sft
- from_resume：0
- use_compile：0
- wandb/swanlab：disabled / offline

## 输出目录

- LoRA v2 adapter：`outputs/lora_customer_service_v2/lora_customer_service_v2_768.pth`
- stdout：`outputs/lora_train_v2_stdout.txt`
- stderr：`outputs/lora_train_v2_stderr.txt`
- config：`experiments/lora_train_v2_config.json`

## 训练结果

- 训练状态：成功
- loss log 数量：60
- loss 起点：3.9860，Epoch 1/3，step 10/200
- loss 终点：2.2107，Epoch 3/3，step 200/200
- LoRA v2 adapter：`outputs/lora_customer_service_v2/lora_customer_service_v2_768.pth`
- adapter 文件大小：798177 bytes，约 0.76 MB
- stderr 大小：125 bytes
- stderr 检查结论：无 Traceback、Error、CUDA out of memory、checkpoint mismatch、NaN 或 inf；仅包含 datasets 生成 train split 的进度输出。
- stdout 检查结论：loss 正常出现，未发现 NaN / inf 或明显异常 loss。

## 输出检查

已运行：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_lora_training_v2_outputs.py
```

检查脚本输出摘要：

- LoRA v2 output directory：存在
- `lora_customer_service_v2_768.pth`：存在
- stdout log：存在
- stderr log：存在
- loss log count：60
- first loss：3.9860
- last loss：2.2107
- suspicious patterns：none

## 下一步

- 使用同一批 `data/baseline_prompts.jsonl` 运行 LoRA v2 推理。
- 对 baseline / LoRA v1 / LoRA v2 做三方对比。
- 重点观察拒答边界、投诉安抚、规则解释和必要信息询问是否比 v1 更稳定。
- 不只凭 loss 判断业务效果，需要结合生成输出和人工/规则评分。
