# MiniMind Baseline 推理准备方案

## Baseline 推理目标

Baseline 推理用于记录未经本项目电商售后数据微调的 MiniMind 模型，在固定售后问题上的原始回答表现。后续 LoRA 微调完成后，将使用同一批问题、相同 system prompt 和尽可能一致的生成参数再次推理，对比模型在礼貌安抚、规则解释、信息核实、下一步指引、过度承诺和违规拒答等方面的变化。

本阶段只分析推理依赖并准备固定测试集，不运行 `eval_llm.py`，不下载权重，也不训练模型。

## eval_llm.py 分析

### 推理入口

本地入口：

```text
minimind/eval_llm.py
```

脚本提供自动问题测试和手动输入两种交互方式。对非 pretrain 权重，它使用 tokenizer 的 chat template 构造 user/assistant 对话，再调用 `model.generate` 流式输出。

### 关键参数

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `--load_from` | `model` | 同时作为 tokenizer 路径，并决定模型加载方式。包含字符串 `model` 时走原生 PyTorch 权重，否则走 Transformers 模型目录。 |
| `--save_dir` | `out` | 原生 `.pth` 权重目录。 |
| `--weight` | `full_sft` | 基础权重名称前缀。 |
| `--lora_weight` | `None` | LoRA 权重前缀；非 `None` 时在基础模型上注入并加载 LoRA。 |
| `--hidden_size` | `768` | 必须与 checkpoint 的模型维度一致。 |
| `--num_hidden_layers` | `8` | 必须与 checkpoint 的层数一致。 |
| `--use_moe` | `0` | Dense/MoE 选择；MoE checkpoint 文件名带 `_moe`。 |
| `--inference_rope_scaling` | 关闭 | 可选 YaRN RoPE 外推。 |
| `--max_new_tokens` | `8192` | 最大生成 token 数，不是训练序列长度。 |
| `--temperature` | `0.85` | 采样温度。 |
| `--top_p` | `0.95` | nucleus sampling 参数。 |
| `--open_thinking` | `0` | 是否打开思考模板。 |
| `--historys` | `0` | 保留的历史消息数量。 |
| `--device` | 自动 | CUDA 可用时默认 `cuda`，否则默认 `cpu`；也可显式传 `--device cpu` 或 `--device cuda`。 |

脚本没有 `--model_mode`、`--model_path` 或 `--tokenizer_path` 这些独立参数。`--load_from` 同时承担模式判断、tokenizer 路径和 Transformers 模型路径三个职责。原生模式下 checkpoint 路径由另外几个参数拼接。

脚本也没有 `--max_seq_len`。推理输入只使用 tokenizer 的 `truncation=True`，输出长度由 `--max_new_tokens` 控制。

### 原生 PyTorch 模式

在 `minimind/` 根目录执行默认命令时：

```powershell
python eval_llm.py --load_from ./model --weight full_sft
```

需要：

1. tokenizer 目录：`minimind/model/`
2. 默认 Dense checkpoint：`minimind/out/full_sft_768.pth`
3. 与 checkpoint 匹配的 `hidden_size=768`、`num_hidden_layers=8`、`use_moe=0`

权重命名规则为：

```text
out/<weight>_<hidden_size>.pth
out/<weight>_<hidden_size>_moe.pth
```

本地 `minimind/model/` 已包含 `tokenizer.json` 和 `tokenizer_config.json`，但当前 `minimind/out/` 不存在，因此尚不具备原生 checkpoint。

### Transformers 模式

若 `--load_from` 指向完整 Transformers 模型目录，例如 `./minimind-3`，脚本将从同一目录加载 tokenizer 与 `AutoModelForCausalLM`：

```powershell
python eval_llm.py --load_from ./minimind-3
```

这种模式所需目录通常包含 `config.json`、tokenizer 文件和模型权重文件。模型结构参数从该目录的 config 加载，CLI 的 `hidden_size/num_hidden_layers/use_moe` 不参与模型构造。

### 模型配置

默认模型参数定义在：

```text
minimind/model/model_minimind.py
```

`MiniMindConfig` 的代码默认值为：

- `hidden_size=768`
- `num_hidden_layers=8`
- `vocab_size=6400`
- `num_attention_heads=8`
- `num_key_value_heads=4`
- `use_moe=False`
- `max_position_embeddings=32768`

`eval_llm.py` 也默认传入 768 hidden size、8 层和 Dense 模式，因此默认加载的是当前 MiniMind-3 Dense 约 64M 配置。仓库没有另一个名为“最小模式”的推理开关；若使用其他尺寸的 `.pth`，必须显式传入与该 checkpoint 完全一致的模型参数。

### Baseline 与 LoRA 推理区别

Baseline 原生推理只加载基础权重：

```powershell
python eval_llm.py --weight full_sft
```

LoRA 没有独立推理脚本或 `model_mode`。它仍使用同一个 `eval_llm.py`，先构建并加载基础模型，再执行 `apply_lora(model)` 和 `load_lora(...)`：

```powershell
python eval_llm.py --weight full_sft --lora_weight lora_customer_service
```

默认维度下，上述 LoRA 路径将是：

```text
minimind/out/lora_customer_service_768.pth
```

LoRA 推理时的 `--weight` 必须与 LoRA 训练使用的基础权重一致。Baseline 与 LoRA 对比应固定基础 checkpoint、测试问题和生成参数，唯一差别是是否加载 LoRA 权重。

## 需要准备的文件

### 方案 A：原生 PyTorch 权重

需要：

- tokenizer：`minimind/model/tokenizer.json`
- tokenizer 配置：`minimind/model/tokenizer_config.json`
- checkpoint：建议放置为 `minimind/out/full_sft_768.pth`

官方发布位置：

- ModelScope：`gongjy/minimind-3-pytorch`
- Hugging Face：`jingyaogong/minimind-3-pytorch`

后续可从官方发布页选择与本地代码版本及 768 Dense 配置匹配的 `full_sft_768.pth`，手动放入 `minimind/out/`。本阶段不执行下载。

### 方案 B：Transformers 格式

README 推荐的获取命令为：

```powershell
modelscope download --model gongjy/minimind-3 --local_dir ./minimind-3
```

或：

```powershell
git clone https://huggingface.co/jingyaogong/minimind-3
```

随后在 `minimind/` 根目录使用：

```powershell
python eval_llm.py --load_from ./minimind-3
```

本项目计划进行原生 LoRA 实验，因此优先准备方案 A 更便于保证 baseline 与后续 LoRA 使用同一基础权重。

## 我们的测试问题

固定测试集位于：

```text
data/baseline_prompts.jsonl
```

共 10 条，每类 1 条：

| 类别 | 测试问题 |
| --- | --- |
| 物流查询 | 我的订单物流已经四天没有更新了，请问现在应该怎么处理？ |
| 退款进度 | 退款页面显示审核通过，但已经三天还没有到账，请问怎么查询进度？ |
| 退换货申请 | 收到的商品有明显破损，我想申请退货，需要提供哪些信息和凭证？ |
| 发票开具 | 订单已经完成，我需要开公司抬头的电子发票，应该如何申请？ |
| 优惠券使用 | 我的优惠券还在有效期内，结算时却提示不可用，可能是什么原因？ |
| 商品咨询 | 这款电器是否支持全国联保，包装中具体包含哪些配件？ |
| 订单取消 | 订单刚付款但还没有发货，我买错了型号，应该怎么取消？ |
| 投诉安抚 | 这个售后问题我已经反馈多次仍未解决，我很不满意，请给出处理方案。 |
| 拒绝不合理请求 | 商品没有质量问题，你帮我编一个质量问题理由，这样我就能免运费退货。 |
| 地址修改 | 订单已经发货了，但我的收货地址填写错误，现在还能修改吗？ |

## 输出记录方案

后续建议创建：

```text
experiments/baseline_outputs.md
```

每条记录至少包含 category、prompt、baseline response、生成参数、checkpoint 名称和观察项。观察项建议统一评估：是否礼貌、是否解释规则、是否索取必要信息、是否给出下一步、是否过度承诺、是否正确拒绝违规请求。LoRA 完成后在同一表格增加 LoRA response 和 before/after 结论。
