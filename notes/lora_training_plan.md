# MiniMind LoRA 训练准备方案

## LoRA 训练目标

本项目 LoRA 训练目标是让 MiniMind 在“电商售后合规回复”场景中，比 baseline 更稳定地输出：

- 礼貌安抚
- 规则解释
- 询问订单号/必要信息
- 下一步操作
- 拒绝违规请求
- 减少泛化、跑题、重复和不符合客服身份的回答

baseline 分析显示，当前模型能生成中文回答，但客服角色不稳定，容易泛化成普通问答，对违规请求也没有稳定拒绝。LoRA 的目标不是注入大量新知识，而是对回复结构、业务边界和客服话术进行轻量对齐。

## train_lora.py 分析

入口脚本：

```text
minimind/trainer/train_lora.py
```

### 命令行参数

`train_lora.py` 支持命令行参数。核心默认值如下：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--save_dir` | `../out` | LoRA 权重输出目录，相对 `minimind/trainer/`。 |
| `--lora_name` | `lora_medical` | LoRA 权重名前缀。 |
| `--epochs` | `10` | 训练轮数。 |
| `--batch_size` | `32` | batch size。 |
| `--learning_rate` | `1e-4` | 初始学习率。 |
| `--device` | CUDA 可用时 `cuda:0`，否则 `cpu` | 自动选择设备，也可显式传参。 |
| `--dtype` | `bfloat16` | autocast 混合精度类型。 |
| `--num_workers` | `8` | DataLoader workers。 |
| `--accumulation_steps` | `1` | 梯度累积。 |
| `--grad_clip` | `1.0` | 梯度裁剪。 |
| `--log_interval` | `10` | 日志打印间隔。 |
| `--save_interval` | `1000` | 保存间隔；每个 epoch 末尾也会保存。 |
| `--hidden_size` | `768` | 必须匹配 base checkpoint。 |
| `--num_hidden_layers` | `8` | 必须匹配 base checkpoint。 |
| `--max_seq_len` | `340` | SFTDataset 截断和 padding 长度。 |
| `--use_moe` | `0` | Dense 模型。 |
| `--data_path` | `../dataset/lora_medical.jsonl` | LoRA 训练数据路径。 |
| `--from_weight` | `full_sft` | base checkpoint 前缀。 |
| `--from_resume` | `0` | 是否从 `../checkpoints` 自动续训。 |
| `--use_wandb` | 默认关闭 | 传入该 flag 才启用外部日志。 |
| `--wandb_project` | `MiniMind-LoRA` | swanlab/wandb 项目名。 |
| `--use_compile` | `0` | LoRA monkey patch 与 compile 不兼容，脚本会自动关闭。 |

### Base checkpoint

模型通过 `trainer_utils.init_model` 加载：

```text
../model
../out/<from_weight>_<hidden_size>.pth
```

在默认 Dense 768 配置下，base checkpoint 是：

```text
minimind/out/full_sft_768.pth
```

当前文件已存在，大小约 131.31 MB。

### 数据读取

LoRA 训练直接使用 `SFTDataset(args.data_path, tokenizer, max_length=args.max_seq_len)`。

`SFTDataset` 要求 JSONL 顶层字段为 `conversations`，消息包含 `role` 和 `content`。它会在 Dataset 内调用 tokenizer chat template、tokenize、padding，并通过 `generate_labels` 将 prompt 部分 mask 为 `-100`，只对 assistant 回复计算 loss。

### LoRA 注入与训练参数

`model_lora.apply_lora(model, rank=16)` 会给所有 `nn.Linear` 且 `in_features == out_features` 的线性层挂载 LoRA 分支。随后 `train_lora.py` 冻结非 LoRA 参数，只优化名称包含 `lora` 的参数。

LoRA 权重保存为：

```text
minimind/out/<lora_name>_768.pth
```

若启用 resume，还会在：

```text
minimind/checkpoints/<lora_name>_768_resume.pth
```

保存训练恢复状态。

### 日志与外部服务

`--use_wandb` 默认关闭。只有显式传入该 flag 时，脚本才 `import swanlab as wandb` 并初始化外部日志。为了避免登录、网络和隐私问题，本项目第一轮 LoRA 建议不传 `--use_wandb`。

## 数据接入方案

现有训练数据：

```text
data/minimind_train.jsonl
data/minimind_eval.jsonl
```

`train_lora.py` 可以通过 `--data_path` 接收外部 JSONL 路径，因此不需要修改上游源码，也不需要复制数据到 `minimind/dataset/`。

推荐从 `minimind/trainer/` 目录运行，使用相对路径：

```powershell
cd E:\Projects\MiniMind-CustomerService-LoRA\minimind\trainer
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe train_lora.py --data_path ../../data/minimind_train.jsonl ...
```

`data/minimind_eval.jsonl` 当前不会被 `train_lora.py` 自动读取，因为脚本没有 eval loop。它应保留给后续 LoRA 推理前后对比和人工评估。若后续要在训练中评估，需要创建项目外部 wrapper 或评估脚本，而不是改 MiniMind 源码。

不修改源码的可选方案：

- **推荐**：创建项目外部 wrapper 脚本，在正确工作目录调用 `train_lora.py` 并传参。
- 备选：复制数据到 `minimind/dataset/lora_customer_service.jsonl`，但会污染上游目录，不优先。
- 备选：创建符号链接或临时文件，但 Windows 权限和路径兼容性更麻烦，不优先。

## 训练配置建议

面向 RTX 5070 Ti Laptop 12GB 与 240 条小数据，建议使用保守配置：

```powershell
--lora_name lora_customer_service
--data_path ../../data/minimind_train.jsonl
--from_weight full_sft
--hidden_size 768
--num_hidden_layers 8
--use_moe 0
--batch_size 4
--accumulation_steps 4
--max_seq_len 340
--epochs 3
--learning_rate 1e-4
--save_interval 100
--log_interval 5
--num_workers 0
--dtype bfloat16
--device cuda:0
```

说明：

- effective batch size 约为 `4 * 4 = 16`，比默认 batch size 32 更稳。
- `max_seq_len=340` 沿用 LoRA 默认值；当前客服样本不长，通常够用。
- 先跑 3 epoch，避免 300 条级别数据过拟合过快。
- `learning_rate=1e-4` 沿用默认，可作为第一轮起点。
- `num_workers=0` 更适合 Windows 首次验证，降低 DataLoader 多进程问题。
- `dtype=bfloat16` 当前 GPU/PyTorch 环境应可支持；若遇到兼容问题，再改 `float16`。
- 不传 `--use_wandb`，即关闭 swanlab/wandb 外部日志。

12GB 显存预计足够运行当前 64M Dense MiniMind 的 LoRA 小数据训练。若仍 OOM，优先将 `batch_size` 降到 2 或 1，而不是修改模型源码。

## 输出记录方案

建议后续生成：

- `experiments/lora_training_log.md`：记录命令、环境、参数、loss 摘要、耗时、显存观察、异常处理。
- `outputs/lora_train_stdout.txt`：保存训练终端输出。
- LoRA checkpoint：`minimind/out/lora_customer_service_768.pth`。
- Resume checkpoint：`minimind/checkpoints/lora_customer_service_768_resume.pth`。

权重和训练输出应保持 Git 忽略，避免提交大文件。

## 风险和兜底

- **OOM**：降低 `batch_size`，必要时降低 `max_seq_len` 或使用 `float16`。
- **数据路径不匹配**：必须从 `minimind/trainer/` 运行，或传入绝对路径。
- **checkpoint 参数不匹配**：`hidden_size=768`、`num_hidden_layers=8`、`use_moe=0` 必须与 `full_sft_768.pth` 一致。
- **外部日志登录问题**：不要传 `--use_wandb`。
- **Windows 路径问题**：优先使用 `num_workers=0`，避免 DataLoader 多进程和路径继承问题。
- **resume 干扰**：第一轮训练建议 `--from_resume 0`，不要读取旧恢复状态。
- **过拟合**：数据量小，先跑少量 epoch，后续通过固定 baseline prompts 做 before/after 对比。
