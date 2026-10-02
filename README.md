# 客服微调

使用真实中文客服对话对 Qwen3.5-4B 进行 4-bit QLoRA 微调，并在独立测试集上验证模型是否学会了数据中的目标回复。

## 最终结果

最终采用 assistant-token 归一化训练得到的 LoRA adapter。测试集包含 120 条未参与训练、并与训练集按源对话隔离的客服回复。

| 指标 | 原始 Qwen3.5-4B | 微调后 | 变化 |
| --- | ---: | ---: | ---: |
| 目标回复 NLL | 3.398 | **1.657** | -51.2% |
| 目标回复困惑度 PPL | 29.90 | **5.24** | -82.5% |
| 字符 bigram F1 | 0.058 | **0.169** | +192% |
| ROUGE-L F1 | 0.117 | **0.266** | +127% |
| 平均回复长度误差 | 140.4 | **31.3** | -77.7% |
| 空回复 | 0 | 0 | 无退化 |
| 严重长度膨胀 | 46 | **0** | -46 |
| 严重长度缩短 | 0 | 9 | 仍需改进 |

120 条测试回复的参考 NLL 全部低于原始模型。结果说明 LoRA 明显提高了模型对目标客服回复分布的拟合能力，同时大幅减少了原始模型的冗长扩写。

当前最佳 adapter：

```text
outputs/qwen35_4b_qlora_dch2_token_v10_run2/best_adapter
```

## 项目内容

- 将本地 DCH-2 客服对话转换为 Qwen messages 格式；
- 对文本进行脱敏，并按源对话分组切分，避免同一段对话跨训练集和测试集；
- 使用 Qwen3.5-4B、4-bit NF4 QLoRA 和 assistant-only loss 完成三轮训练；
- 依据开发集损失选择 checkpoint，不使用测试集挑选模型；
- 在同一批测试样本、相同解码参数下比较原始模型与 LoRA；
- 同时检查参考 NLL、文本重合度、空回复、长度异常和重复集中。

## 数据与训练配置

| 项目 | 配置 |
| --- | --- |
| 训练数据 | 5,888 条 |
| 开发数据 | 646 条 |
| 独立测试数据 | 120 条 |
| 基座模型 | Qwen3.5-4B |
| 量化 | 4-bit NF4 double quantization |
| LoRA | rank 8，alpha 16，dropout 0.05 |
| 训练轮数 | 3 |
| 学习率 | `2e-4` |
| 最大长度 | 512 tokens |
| 随机种子 | 42 |
| 最佳 checkpoint | epoch 2 |

数据仅用于本地非商业研究和学习。原始对话、处理后的私有数据、模型权重和生成结果均不提交到公开仓库。

## 运行方法

### 1. 环境

先根据本机 CUDA 驱动安装匹配的 PyTorch，再安装其余依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r requirements-qwen-qlora.txt
```

### 2. 准备数据

```powershell
.\.venv\Scripts\python.exe scripts\build_qwen35_dch2_protocol_v8.py --help
```

该脚本生成按源对话隔离的 `train.jsonl`、`dev.jsonl` 和冻结测试集。DCH-2 原始文件需要由使用者根据其数据协议自行准备。

### 3. 训练最佳配置

```powershell
.\.venv\Scripts\python.exe scripts\train_qwen35_qlora_v8.py `
  --model_name_or_path models\qwen3_5_4b `
  --train_file outputs\qwen35_dch2_protocol_v8\train.jsonl `
  --dev_file outputs\qwen35_dch2_protocol_v8\dev.jsonl `
  --output_dir outputs\qwen35_customer_service_run `
  --num_train_epochs 3 `
  --per_device_train_batch_size 1 `
  --per_device_eval_batch_size 1 `
  --gradient_accumulation_steps 8 `
  --learning_rate 0.0002 `
  --max_seq_length 512 `
  --seed 42 `
  --loss_normalization assistant_token
```

### 4. 单条推理

```powershell
.\.venv\Scripts\python.exe scripts\infer_qwen35_lora.py `
  --prompt "我的退款还没有到账，请问怎么查询？"
```

脚本默认加载本项目验证效果最好的 adapter，关闭 thinking，并使用确定性解码。

### 5. 评估

```powershell
# 目标回复 NLL / PPL
.\.venv\Scripts\python.exe scripts\evaluate_qwen35_reference_nll_v8.py --help

# 固定样本生成
.\.venv\Scripts\python.exe scripts\build_qwen_frozen_eval_v7.py --help

# 参考重合度与长度、重复退化检查
.\.venv\Scripts\python.exe scripts\analyze_qwen35_reference_alignment_v8.py --help
```

评估脚本默认拒绝覆盖已有输出目录，避免无意中改写实验结果。

## 核心文件

```text
requirements-qwen-qlora.txt
scripts/
  build_qwen35_dch2_protocol_v8.py
  train_qwen35_qlora_v8.py
  infer_qwen35_lora.py
  build_qwen_frozen_eval_v7.py
  evaluate_qwen35_reference_nll_v8.py
  analyze_qwen35_reference_alignment_v8.py
```

开发过程中还比较了不同的损失归一化和短回复权重方案，最终保留综合指标最好的 assistant-token 归一化配置。实验过程不是项目首页的重点。

## 局限性

- 当前结果证明模型更接近给定客服回复，不代表生产环境中的客服质量；
- 模型未连接订单或物流系统，不能把生成内容当作真实订单状态，生产使用前需要接入检索与事实校验；
- 字符重合指标不能完全表示语义等价；
- 最佳模型仍有 9 条严重缩短回复，长流程回答覆盖需要继续改进；
- 没有用这 120 条测试数据反复选择训练规则或修改超参数。
