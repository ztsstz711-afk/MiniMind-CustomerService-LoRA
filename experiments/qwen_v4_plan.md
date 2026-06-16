# Qwen v4 Plan

## 为什么从 MiniMind 迁移到 Qwen2.5

v1 到 v3 已经完整跑通 MiniMind 的低资源 LoRA 实验链路：数据构造、baseline、LoRA v1/v2、100 条 eval prompts、rule-based rubric 自动评分。这个闭环证明了项目工程链路是可复现的，但也暴露出 MiniMind 小模型的能力边界。

迁移到 Qwen2.5 的目的不是推翻 MiniMind 实验，而是用同一套数据和评估体系，验证更强基座模型是否能更稳定地吸收电商售后合规规则。

## MiniMind 的局限

- 模型参数小，复杂售后规则理解能力有限。
- 拒绝不合理请求仍不稳定，容易被用户问题中的“退款、质量问题、发票”等表层语义带偏。
- 生成质量有限，仍出现重复、泛化、偏题和偶发替换字符。
- loss 下降不等于业务效果明显提升，v3 自动评分也只能说明趋势。

## v4 目标

v4 的核心目标是：更强基座模型 + 同一套 v2 数据 + 同一套 v3 评估集，横向对比 MiniMind LoRA v2 与 Qwen2.5 LoRA 的效果差异。

对比维度：

- 礼貌安抚
- 规则解释
- 询问订单号或必要信息
- 下一步操作
- 拒绝不合理请求
- 重复、乱码、偏题等生成稳定性

## 模型选择

主线模型：

- `Qwen/Qwen2.5-1.5B-Instruct`

保底模型：

- `Qwen/Qwen2.5-0.5B-Instruct`

选择理由：

- Qwen2.5 Instruct 系列具备更强的指令遵循能力。
- 0.5B / 1.5B 仍属于小模型范围，适合个人 GPU 做 LoRA 实验。
- 与 MiniMind 相比，Qwen2.5 更接近真实应用中常见的开源基座模型。

## 训练方式

- 优先使用 PEFT LoRA。
- 暂不把 4bit QLoRA 作为第一方案，因为 Windows 环境下 `bitsandbytes` 可能不稳定。
- 如果 CUDA 可用且显存允许，先尝试 bf16/fp16 LoRA。
- 训练前先做小样本 smoke test，确认 tokenizer、chat template、padding、labels 和 adapter 保存逻辑正常。

## 评估方式

复用 v3 评估体系：

- eval prompts：`data/eval_prompts_v3.jsonl`
- rule-based rubric：`scripts/evaluate_outputs_v3.py`

后续 Qwen baseline / Qwen LoRA 输出也应保持与 v3 评分脚本兼容：

- `id`
- `category`
- `prompt`
- `expected_behavior`
- `required_elements`
- `forbidden_elements`
- `difficulty`
- `tags`
- `model_name`
- `output`
- `model_output`

## 后续步骤

1. 环境检查，确认 PyTorch、CUDA、Transformers、Datasets、PEFT、Accelerate、TRL。
2. 将 v2 数据转换为 Qwen / TRL SFTTrainer 友好的 `messages` 格式。
3. 下载 Qwen2.5 模型权重。
4. 运行 Qwen baseline 推理。
5. 先做小样本 LoRA smoke test。
6. 正式 LoRA 训练。
7. 使用 100 条 eval prompts 运行 Qwen LoRA 推理。
8. 复用 v3 rubric 自动评分。
9. 生成 MiniMind vs Qwen 的横向对比报告。

## 当前状态

- 暂未下载 Qwen 模型。
- 暂未训练 Qwen LoRA。
- 当前阶段只做环境检查、数据格式转换和脚本草案准备。

## 环境检查结果

检查命令：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/check_qwen_v4_environment.py
```

当前结果：

- Python executable：`C:\Users\20112\anaconda3\envs\minimind-lora\python.exe`
- Python：3.10.20
- torch：2.12.0.dev20260408+cu128
- CUDA available：True
- CUDA version：12.8
- GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU
- transformers：available，4.57.6
- datasets：available，3.6.0
- accelerate：available，1.14.0
- trl：available，0.13.0
- peft：unavailable，当前环境缺少 `peft`
- bitsandbytes：unavailable

建议：

- CUDA 可用，可以优先尝试 Qwen2.5-1.5B-Instruct bf16/fp16 LoRA。
- `bitsandbytes` 不可用，因此暂不建议先做 4bit QLoRA。
- 正式训练 Qwen LoRA 前，需要先安装或修复 `peft`。

## 数据转换结果

已生成 Qwen / TRL SFTTrainer 友好的 `messages` 格式数据：

- `data/qwen_train_v4.jsonl`：800 条
- `data/qwen_eval_v4.jsonl`：200 条

检查结果：

- train rows：800
- eval rows：200
- messages 包含 system / user / assistant 三轮
- assistant content 非空
- metadata 保留 `category`、`difficulty`、`tags`
- duplicate user+assistant pairs：0
