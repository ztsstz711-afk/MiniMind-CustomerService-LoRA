# MiniMind 本地代码集成分析

> 分析日期：2026-06-16  
> 分析依据：当前项目中的本地仓库 `minimind/`。本阶段仅静态阅读代码，未训练、未安装依赖、未下载权重、未修改 MiniMind 源码。

## MiniMind 仓库结构概览

| 相对路径 | 作用 |
| --- | --- |
| `minimind/README.md` | 官方项目说明、训练命令、数据格式示例和各阶段流程。 |
| `minimind/trainer/` | Pretrain、全参数 SFT、LoRA、DPO、PPO、GRPO、Agent 等训练入口。 |
| `minimind/dataset/lm_dataset.py` | 定义 `PretrainDataset`、`SFTDataset` 等数据读取与 token/label 构造逻辑。 |
| `minimind/model/model_minimind.py` | MiniMind 配置、Transformer 模型、Causal LM loss 和生成实现。 |
| `minimind/model/model_lora.py` | 原生 LoRA 注入、读取、保存和合并逻辑。 |
| `minimind/model/tokenizer.json` | tokenizer 词表及分词模型。 |
| `minimind/model/tokenizer_config.json` | BOS/EOS/PAD token 与 chat template。 |
| `minimind/trainer/trainer_utils.py` | tokenizer/模型初始化、权重加载、checkpoint、DDP、日志等公共逻辑。 |
| `minimind/eval_llm.py` | 命令行交互推理，可加载原生 MiniMind 权重与 LoRA。 |
| `minimind/scripts/` | OpenAI API 服务、WebUI、API 客户端和模型转换工具。 |

## 训练入口

以下脚本均在本地文件系统中实际存在，并由其 `if __name__ == "__main__"`、参数定义和 Dataset 初始化代码确认。

### Pretrain

- 入口：`minimind/trainer/train_pretrain.py`
- 默认数据：`../dataset/pretrain_t2t_mini.jsonl`
- Dataset：`PretrainDataset`
- 默认 `from_weight=none`，即从头预训练。

### 全参数 SFT

- 入口：`minimind/trainer/train_full_sft.py`
- 默认数据：`../dataset/sft_t2t_mini.jsonl`
- Dataset：`SFTDataset`
- 默认 `from_weight=pretrain`，加载预训练权重后进行全参数 SFT。

### LoRA

- 入口：`minimind/trainer/train_lora.py`
- 默认数据：`../dataset/lora_medical.jsonl`
- Dataset：与全参数 SFT 相同，都是 `SFTDataset`。
- 默认 `from_weight=full_sft`。
- 脚本调用 `apply_lora(model)`，随后冻结所有名称不含 `lora` 的参数，只优化 LoRA 参数。

### 推理 / Chat

- 主要 CLI 推理入口：`minimind/eval_llm.py`
- OpenAI 兼容 API 服务：`minimind/scripts/serve_openai_api.py`
- Streamlit WebUI：`minimind/scripts/web_demo.py`
- OpenAI API 客户端示例：`minimind/scripts/chat_api.py`
- Tool Call 评测入口：`minimind/scripts/eval_toolcall.py`

`eval_llm.py` 默认加载 `model/` 中的 tokenizer 和 `out/full_sft_*.pth`。传入 `--lora_weight` 后，会先执行 `apply_lora`，再加载对应 LoRA 权重。对于非 `model` 路径，它使用 `AutoModelForCausalLM.from_pretrained` 加载 Transformers 格式模型。

README 与脚本中的相对路径以从 `minimind/trainer/` 执行为前提。后续若从项目根目录运行，应显式传入正确的 `--data_path` 和权重路径。

## 数据读取逻辑

### Pretrain 数据

`minimind/trainer/train_pretrain.py` 的默认路径是：

```text
../dataset/pretrain_t2t_mini.jsonl
```

`PretrainDataset` 使用 Hugging Face `load_dataset("json", ...)` 读取，样本需要 `text` 字段：

```json
{"text":"用于 next-token prediction 的连续文本"}
```

### SFT 数据

`minimind/trainer/train_full_sft.py` 的默认路径是：

```text
../dataset/sft_t2t_mini.jsonl
```

官方 README 还说明完整数据文件为 `sft_t2t.jsonl`。两者都是 JSONL，即每行一个 JSON 对象。

### LoRA 数据

`minimind/trainer/train_lora.py` 的默认路径是：

```text
../dataset/lora_medical.jsonl
```

LoRA 并没有单独的数据类或独立格式，而是直接复用 `SFTDataset`，因此 SFT 和 LoRA 输入格式一致。`lora_medical.jsonl` 只是官方的垂直领域命名示例，可通过 `--data_path` 指向其他 JSONL 文件。

### SFT / LoRA 样本字段

顶层必须包含 `conversations`，其值为消息数组。普通单轮数据格式为：

```json
{"conversations":[{"role":"user","content":"用户问题"},{"role":"assistant","content":"模型回答"}]}
```

也支持显式 system 消息和多轮对话：

```json
{"conversations":[{"role":"system","content":"你是电商售后客服。"},{"role":"user","content":"用户问题"},{"role":"assistant","content":"客服回答"}]}
```

代码中的 `Features` 还声明了每条消息可能出现的字段：

- `role`
- `content`
- `reasoning_content`
- `tools`
- `tool_calls`

普通客服 SFT 只需要 `role` 和 `content`。其余字段服务于思考数据和 Tool Call。

结论：

- 使用 `conversations`，不是顶层 `messages`。
- 不读取 `instruction/input/output` 格式。
- 文件由 `load_dataset("json", data_files=..., split="train")` 读取；仓库约定扩展名为 `.jsonl`。
- 不需要提前 tokenize。

### Tokenizer 调用位置

训练入口通过 `minimind/trainer/trainer_utils.py` 的 `init_model` 调用：

```python
AutoTokenizer.from_pretrained('../model')
```

`SFTDataset.__getitem__` 的处理顺序是：

1. 读取 `sample['conversations']`。
2. 调用 `pre_processing_chat`；若样本没有 system 消息，有 20% 概率加入通用 system prompt。
3. 调用 `tokenizer.apply_chat_template(..., tokenize=False)` 拼出完整对话文本。
4. 调用 `self.tokenizer(prompt).input_ids` 执行 tokenize。
5. 截断到 `max_length`，再使用 `pad_token_id` 补齐定长序列。
6. 调用 `generate_labels(input_ids)` 生成 labels。

`tokenizer_config.json` 中的关键 token 是：

- BOS：`<|im_start|>`
- EOS：`<|im_end|>`
- PAD：`<|endoftext|>`

### Labels 与 answer-only loss

`SFTDataset.generate_labels` 先把所有 label 初始化为 `-100`，然后搜索：

```text
<|im_start|>assistant\n ... <|im_end|>\n
```

只有 assistant 开始标记之后，到 assistant 结束标记为止的 token 会被复制为真实 labels。system、user、其他 prompt 内容和 padding 均保持 `-100`。

`minimind/model/model_minimind.py` 在 forward 中将 logits 与 labels 左右错开一个 token，并调用：

```python
F.cross_entropy(..., ignore_index=-100)
```

因此可以确认：**prompt 部分被 mask，SFT/LoRA 只对 assistant answer token（包含结束标记）计算语言模型 loss。** 多轮数据中，每一段 assistant 回复都会参与 loss。

### DataLoader / collate

SFT 和 LoRA 入口都直接构造：

```python
DataLoader(train_ds, batch_sampler=..., num_workers=..., pin_memory=True)
```

代码没有传入自定义 `collate_fn`。由于 `SFTDataset` 已将每个样本 padding 到固定 `max_length` 并返回两个 tensor，PyTorch 默认 collate 会直接将其堆叠为 batch。

当前两个入口都只创建训练 DataLoader，没有独立的 `eval_data_path`、验证 DataLoader 或验证循环。

## 我们当前数据能否直接使用

当前数据：

- `data/train.jsonl`
- `data/eval.jsonl`

字段：

- `instruction`
- `input`
- `output`
- `category`

结论：**不能直接接入当前 MiniMind 的 `SFTDataset`。** Dataset 会访问 `sample['conversations']`，当前样本没有该字段，会读取失败。

推荐转换为：

```json
{"conversations":[{"role":"system","content":"你是电商平台售后客服。请礼貌安抚用户，解释适用规则，核实必要信息，给出下一步操作，不作无法兑现的承诺，并拒绝违规请求。"},{"role":"user","content":"退款申请通过了，为什么钱还没到账？"},{"role":"assistant","content":"您好，理解您现在的着急和不便……"}]}
```

字段映射：

| 当前字段 | 转换结果 |
| --- | --- |
| `instruction` | 可转为 system 内容，但建议首版统一使用固定的客服合规 system prompt。 |
| `input` | `role=user` 的 `content`。 |
| `output` | `role=assistant` 的 `content`。 |
| `category` | 不拼入训练文本，用于转换统计、分层评测和错误分析。 |

显式提供固定 system 消息后，`pre_processing_chat` 不会随机插入 MiniMind 的通用 system prompt，客服身份会更稳定。

`eval.jsonl` 也需要转换，但 MiniMind 当前 SFT/LoRA 训练入口不会自动使用它。它应留给后续 baseline 与 LoRA 的独立推理评测脚本。

## 下一步转换脚本方案

建议创建：

```text
scripts/convert_to_minimind_format.py
```

脚本职责：

1. 读取 `data/train.jsonl` 和 `data/eval.jsonl`。
2. 校验每条记录包含非空的 `instruction/input/output/category`。
3. 将 `input` 映射为 user 消息，将 `output` 映射为 assistant 消息。
4. 在每条对话开头加入统一的电商售后合规 system prompt。
5. 输出标准 UTF-8 JSONL，写入时使用 `ensure_ascii=False`。
6. 保证转换前后样本数一致，并打印 train/eval 数量与 category 分布。
7. 校验角色顺序为 `system -> user -> assistant`，最后一条 assistant 内容非空。
8. 不提前 tokenize；tokenize 由 MiniMind 的 `SFTDataset` 在运行时完成。

推荐输出到当前项目自己的 `data/`：

```text
data/minimind_train.jsonl
data/minimind_eval.jsonl
```

**不需要复制到 `minimind/dataset/` 或不存在的 `minimind/data/`。** 保持业务数据与上游仓库解耦更便于更新 MiniMind，也避免污染上游 Git 状态。未来训练时通过 `--data_path` 显式传入，例如从 `minimind/trainer/` 运行时指向：

```text
../../data/minimind_train.jsonl
```

正式训练前还应检查一个数据划分风险：当前每个用户问题有 3 条回复变体，随机逐行划分可能让同一 `input` 同时进入 train 和 eval。更可靠的方案是按 `input` 分组后再做 8:2 划分，避免评测泄漏。

## 本地代码依据

- `minimind/trainer/train_pretrain.py`：默认数据路径和 `PretrainDataset` 初始化。
- `minimind/trainer/train_full_sft.py`：默认 SFT 路径、`SFTDataset` 和 DataLoader。
- `minimind/trainer/train_lora.py`：默认 LoRA 路径、LoRA 参数冻结及 `SFTDataset`。
- `minimind/dataset/lm_dataset.py`：JSONL 读取、`conversations` schema、chat template、tokenize 和 labels。
- `minimind/trainer/trainer_utils.py`：从 `../model` 初始化 tokenizer。
- `minimind/model/tokenizer_config.json`：特殊 token 与 chat template。
- `minimind/model/model_minimind.py`：shifted causal LM loss 与 `ignore_index=-100`。
- `minimind/eval_llm.py`：CLI 推理和 LoRA 权重加载。
