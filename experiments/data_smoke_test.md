# MiniMind 数据 Smoke Test

## 检查信息

- 检查时间：2026-06-16 01:49:29 +08:00
- 检查脚本：`scripts/smoke_test_minimind_data.py`
- 训练数据：`data/minimind_train.jsonl`
- 评估数据：`data/minimind_eval.jsonl`
- 检查方式：使用 Python 标准库逐行解析和校验，不执行训练、不加载模型权重。

## 本地代码依据

- `minimind/trainer/train_full_sft.py` 通过 `--data_path` 将 JSONL 路径传给 `SFTDataset`，默认读取 `../dataset/sft_t2t_mini.jsonl`。
- `minimind/trainer/train_lora.py` 使用同一个 `SFTDataset`，默认读取 `../dataset/lora_medical.jsonl`。
- `minimind/dataset/lm_dataset.py` 使用 `load_dataset("json", ...)` 读取数据，并访问顶层 `conversations`。
- 普通对话消息使用 `role` 和 `content`；不要求 `id`、`source` 或 `category`。
- `SFTDataset` 使用 tokenizer chat template 处理消息，Dataset 内完成 tokenize、padding 和 answer labels 构造。
- DataLoader 没有自定义 `collate_fn`，直接堆叠 Dataset 返回的定长 tensor。

## 检查结果

| 数据集 | 样本数量 | system | user | assistant |
| --- | ---: | ---: | ---: | ---: |
| train | 240 | 240 | 240 | 240 |
| eval | 60 | 60 | 60 | 60 |

数据格式：JSONL，每行一个对象，顶层字段为 `conversations`。每条样本均为三轮消息：

```text
system -> user -> assistant
```

已通过以下检查：

- 每一行均为合法 JSON。
- 顶层包含 `conversations`，且其类型为 list。
- 每条消息均包含 `role` 和 `content`。
- role 仅包含 `system`、`user`、`assistant`。
- 每条样本至少包含 user 和 assistant。
- 所有 assistant content 均为非空字符串。
- 数据结构与本地 MiniMind `SFTDataset` 的普通 SFT / LoRA 输入要求一致。

## 结论

**通过。** 脚本输出：`MiniMind data smoke test passed.`

本次是结构级 smoke test，未实例化 MiniMind tokenizer 或 Dataset，因为本阶段不安装依赖。根据本地代码静态核对，当前数据无需额外的 `id`、`source` 或 `category` 字段，也无需提前 tokenize。

## 后续计划

1. 按 `input` 分组重新检查 train/eval 是否存在问题级数据泄漏。
2. 在已有运行环境中使用 MiniMind tokenizer 实例化少量 `SFTDataset` 样本，检查 token 长度和有效 answer labels。
3. 准备 MiniMind baseline 推理问题集，不启动训练。
4. 确认基础权重与显存方案后，再设计 LoRA 实验配置。
