# MiniMind Checkpoint 下载方案

## 当前缺失文件

当前原生 PyTorch baseline 推理缺少：

```text
minimind/out/full_sft_768.pth
```

`minimind/eval_llm.py` 的默认参数为 `save_dir=out`、`weight=full_sft`、`hidden_size=768`、`use_moe=0`，因此会从 MiniMind 根目录解析出：

```text
./out/full_sft_768.pth
```

本地 tokenizer 已存在于 `minimind/model/`，当前缺失的是上述基础模型权重以及尚未创建的 `minimind/out/` 目录。

## 官方推荐 Checkpoint 来源

本地 `minimind/README.md` 提供了两类官方模型来源。

### 原生 PyTorch `.pth` 权重

这是本项目后续原生 LoRA 实验优先采用的方式。

- ModelScope：`https://www.modelscope.cn/models/gongjy/minimind-3-pytorch`
- HuggingFace：`https://huggingface.co/jingyaogong/minimind-3-pytorch`

README 在测试 SFT 权重部分明确链接到 ModelScope 文件页：

- `https://www.modelscope.cn/models/gongjy/minimind-3-pytorch/files`

README 给出的 Dense 权重命名规则为：

```text
Pretrain: pretrain_{hidden_size}.pth
SFT:      full_sft_{hidden_size}.pth
LoRA:     lora_xxx_{hidden_size}.pth
```

因此默认 768 Dense baseline 所需文件是 `full_sft_768.pth`。MoE 权重会额外带 `_moe` 后缀，本项目当前不需要 MoE checkpoint。

### Transformers 格式模型

官方还发布完整的 Transformers 格式 `minimind-3`，其中包含 config、tokenizer 和模型权重：

- ModelScope：`gongjy/minimind-3`
- HuggingFace：`jingyaogong/minimind-3`

该方案可直接用于 `eval_llm.py --load_from ./minimind-3`，但本项目计划使用 MiniMind 原生 LoRA 训练链路，因此优先准备原生 `full_sft_768.pth`，更容易保证 baseline 与 LoRA 使用同一基础权重。

### 其他来源

本地 README 未提供百度网盘或其他网盘形式的 checkpoint 下载来源。当前应只使用 README 指向的官方 ModelScope 或 HuggingFace 发布页。

## 推荐下载命令

### README 原文命令：Transformers 格式

README 对完整 Transformers 模型给出了以下明确命令：

```bash
modelscope download --model gongjy/minimind-3 --local_dir ./minimind-3
```

```bash
git clone https://huggingface.co/jingyaogong/minimind-3
```

对应推理命令是：

```bash
python eval_llm.py --load_from ./minimind-3
```

### 根据 README 整理：原生 `.pth` 权重

README 没有给出下载单个 `full_sft_768.pth` 的 CLI 命令，只要求将待测试的 `.pth` 放入 `./out/`，并提供官方文件页。因此建议按以下步骤操作：

1. 打开官方 ModelScope 文件页 `gongjy/minimind-3-pytorch/files`，或 HuggingFace 仓库 `jingyaogong/minimind-3-pytorch`。
2. 确认发布文件中存在与当前代码匹配的 Dense SFT 权重 `full_sft_768.pth`。
3. 只下载该文件，不需要下载其他训练阶段权重。
4. 在 `minimind/` 下创建 `out/` 目录。
5. 将文件保存为 `minimind/out/full_sft_768.pth`。
6. 运行 `scripts/check_checkpoint_ready.py` 验证文件与 tokenizer 是否齐全。

上述步骤是根据 README 的官方链接、文件命名表和 `eval_llm.py` 路径逻辑整理，并非 README 中现成的单文件下载命令。

## 下载后应放置的位置

必需文件：

```text
minimind/out/full_sft_768.pth
minimind/model/tokenizer.json
minimind/model/tokenizer_config.json
data/baseline_prompts.jsonl
```

其中 tokenizer 和 baseline prompts 当前已经存在。原生 `.pth` 模式不需要额外复制 tokenizer，因为 `--load_from ./model` 会直接读取 `minimind/model/`。

后续应从 `minimind/` 根目录运行原生推理，使相对路径与脚本一致。当前阶段不运行：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe eval_llm.py --load_from ./model --weight full_sft --hidden_size 768 --num_hidden_layers 8 --use_moe 0
```

## 风险和注意事项

- 不要将大型 checkpoint 提交到 Git。
- 项目根 `.gitignore` 已包含 `*.pth`、`*.pt`、`*.bin`、`*.safetensors` 和 `checkpoints/`，因此 `.pth` 会被全局忽略。
- `minimind/.gitignore` 也应保持上游原状；不需要为下载权重修改 MiniMind 源码或配置。
- 下载前确认磁盘空间，并为下载临时文件和最终 checkpoint 预留余量。
- 只使用官方 ModelScope/HuggingFace 页面，核对文件名、模型版本、Dense/MoE 类型和 `hidden_size=768`。
- `checkpoints/*_resume.pth` 是训练恢复状态，不等同于 `out/full_sft_768.pth` 推理权重，不应混用。
- 不要把 Transformers 整包权重误命名成单个 `.pth`；两种加载模式不同。
- 下载后先运行 `scripts/check_checkpoint_ready.py`，确认 checkpoint、tokenizer 和测试问题齐全，再进入 baseline 推理。
