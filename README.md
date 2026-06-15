# MiniMind-CustomerService-LoRA：电商售后合规回复 LoRA 微调实验

## 项目简介

这是一个面向“电商售后合规回复”的低资源小模型 SFT / LoRA 微调实验。项目基于 MiniMind，完整跑通了数据构造、MiniMind 对话格式转换、baseline 推理、LoRA 微调、LoRA 推理和 before/after 对比分析。

需要强调：本项目不是工业级客服系统，也不声称微调后模型已达到线上可用效果。它更像一个可复现的学习型实验，用来观察小模型在少量垂直数据上的风格迁移、合规边界学习和失败模式。

## 项目动机

选择电商售后合规回复，是因为这个场景同时适合做业务规则验证和低资源微调实验：

- 场景规则相对明确，例如物流、退款、退换货、发票、优惠券和地址修改。
- 回复质量不只看“能不能回答”，还要看是否安抚用户、解释规则、询问信息、给出下一步，并避免乱承诺。
- 对虚假退款、伪造理由、泄露隐私等请求，需要稳定拒绝，适合观察 SFT / LoRA 对合规边界的影响。
- 数据规模可以从小样本起步，适合验证低资源 LoRA 流程。

## 技术栈

- Python
- PyTorch
- MiniMind
- LoRA
- Transformers / tokenizer
- JSONL 数据处理
- CUDA / GPU

## 实验流程

1. 构造电商售后 SFT 数据。
2. 划分 train / eval。
3. 转换为 MiniMind `conversations` 格式。
4. 进行数据 smoke test。
5. 准备 MiniMind baseline checkpoint。
6. 运行 baseline 推理。
7. 使用 LoRA 进行小数据微调。
8. 运行 LoRA 推理。
9. 进行 before/after 对比分析。

## 数据集

原始数据格式为 JSONL，每条包含：

```json
{
  "instruction": "...",
  "input": "...",
  "output": "...",
  "category": "退款进度"
}
```

数据规模：

- 总数据：300
- train：240
- eval：60
- 类别：10 类

场景类别：

- 物流查询
- 退款进度
- 退换货申请
- 发票开具
- 优惠券使用
- 商品咨询
- 订单取消
- 投诉安抚
- 拒绝不合理请求
- 地址修改

转换后的 MiniMind 格式为：

```json
{
  "conversations": [
    {"role": "system", "content": "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。..."},
    {"role": "user", "content": "场景：退款进度\n用户问题：...\n请生成一段客服回复。"},
    {"role": "assistant", "content": "..."}
  ]
}
```

## 模型与训练配置

- base checkpoint：`full_sft_768.pth`
- hidden_size：768
- num_hidden_layers：8
- use_moe：0
- batch_size：4
- accumulation_steps：4
- effective batch size：16
- epochs：3
- learning_rate：1e-4
- max_seq_len：340
- GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU
- LoRA 输出：`outputs/lora_customer_service/lora_customer_service_768.pth`

## 实验结果

- LoRA loss：3.7383 -> 2.8888
- LoRA adapter size：约 0.76 MB
- baseline prompts：10 条
- before/after 对比：已完成

关键实验文件：

- baseline 输出：`experiments/baseline_outputs.md`
- baseline 分析：`experiments/baseline_analysis.md`
- LoRA 训练日志：`experiments/lora_training_log.md`
- LoRA 输出：`experiments/lora_outputs.md`
- before/after 对比：`experiments/before_after_comparison.md`
- 最终分析：`experiments/final_lora_analysis.md`

## 结果分析

v1 的结论比较朴素，但很重要：

- LoRA 后模型开始拟合电商售后客服数据，loss 明显下降。
- 训练链路和推理链路完整跑通，adapter 体积极小，符合参数高效微调预期。
- 但业务效果提升有限。
- 礼貌安抚增强不明显。
- 对违规请求仍未稳定拒绝。
- 小模型和小数据限制明显，部分回答仍然泛化、偏题或重复。

这说明“能训练成功”不等于“业务效果达标”。这个项目的价值不在于夸大模型能力，而在于完整记录了低资源 LoRA 的可行性、收益和局限。

## 项目亮点

- 完整复现低资源 LoRA 微调链路。
- 有 baseline 和 LoRA 的 before/after 对比。
- 有训练日志和 loss 记录。
- 有 LoRA adapter size 分析。
- 有失败案例和局限性分析。
- 不夸大模型效果，明确说明小数据、小模型下的真实限制。
- 数据、脚本、实验记录分层清晰，便于迁移到其他小模型。

## 项目局限

- 数据规模小，仅 300 条左右。
- 模型参数小，不代表工业级客服系统效果。
- 评估样本少，固定测试集只有 10 条。
- 自动评估规则简单，主要基于关键词，不足以替代人工评估。
- 拒答边界样本仍然不足。
- 当前没有进行多轮客服对话训练。

## 后续计划

- 扩展到 1000+ 高质量售后样本。
- 增加拒答边界与 hard cases。
- 加入人工评分或 LLM-as-Judge。
- 构建更系统的评估集。
- 迁移到 Qwen-0.5B / Qwen-1.5B LoRA。
- 对比 MiniMind vs Qwen LoRA 效果。

## 如何运行

以下命令默认在项目根目录执行。Python 环境示例：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe
```

### 1. 构造与划分数据

```powershell
python scripts/build_dataset.py
python scripts/split_dataset.py
```

### 2. 转换为 MiniMind 格式

```powershell
python scripts/convert_to_minimind_format.py
```

### 3. 数据 smoke test

```powershell
python scripts/smoke_test_minimind_data.py
```

### 4. 运行环境检查

```powershell
python scripts/check_runtime.py
```

### 5. baseline 推理

需要先准备 MiniMind 官方 `full_sft_768.pth` checkpoint：

```powershell
python scripts/check_checkpoint_ready.py
python scripts/run_baseline_inference.py
```

### 6. LoRA 训练

```powershell
python scripts/check_lora_training_requirements.py
python scripts/run_lora_training.py
python scripts/check_lora_training_outputs.py
```

### 7. LoRA 推理

```powershell
python scripts/check_lora_inference_requirements.py
python scripts/run_lora_inference.py
```

### 8. before/after 对比

```powershell
python scripts/compare_baseline_lora.py
```

## 当前进度

- [x] 数据生成与划分
- [x] MiniMind `conversations` 格式转换
- [x] 数据 smoke test
- [x] CUDA 环境检查
- [x] baseline checkpoint 准备
- [x] baseline 推理
- [x] baseline 分析
- [x] LoRA 训练
- [x] LoRA 推理
- [x] before/after 对比
- [x] final analysis 完成
- [x] v1 completed
