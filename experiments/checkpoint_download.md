# MiniMind Baseline Checkpoint 下载记录

## 下载结果

- 状态：已手动下载成功
- 下载来源：MiniMind 官方 PyTorch checkpoint，来源可为 ModelScope `gongjy/minimind-3-pytorch` 或 HuggingFace `jingyaogong/minimind-3-pytorch`
- checkpoint 文件：`full_sft_768.pth`
- checkpoint 路径：`E:\Projects\MiniMind-CustomerService-LoRA\minimind\out\full_sft_768.pth`
- 文件大小：131.31 MB
- ready：True

## check_checkpoint_ready.py 输出

```text
Checkpoint found: E:\Projects\MiniMind-CustomerService-LoRA\minimind\out\full_sft_768.pth
Checkpoint size: 131.31 MB
Tokenizer file found: E:\Projects\MiniMind-CustomerService-LoRA\minimind\model\tokenizer.json
Tokenizer file found: E:\Projects\MiniMind-CustomerService-LoRA\minimind\model\tokenizer_config.json
Baseline prompts found: E:\Projects\MiniMind-CustomerService-LoRA\data\baseline_prompts.jsonl
Checkpoint ready: True
```

## Git 忽略规则

根目录 `.gitignore` 已包含：

```text
minimind/out/
*.pth
*.pt
*.bin
*.safetensors
```

checkpoint 不应提交到 Git。

## 下一步

可以进入 baseline 推理阶段，使用 `data/baseline_prompts.jsonl` 中的 10 条售后问题生成微调前回答，并保存到：

- `experiments/baseline_outputs.md`
- `outputs/baseline_outputs.jsonl`
