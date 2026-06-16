# Qwen v4 Model Smoke Test

## 测试目标

验证 `Qwen/Qwen2.5-1.5B-Instruct` 能否在当前本机环境中正常下载、加载并生成一段电商售后客服回复。

本阶段只做模型加载和单条推理 smoke test，不训练、不做 LoRA、不修改 MiniMind 源码。

## 模型名

- `Qwen/Qwen2.5-1.5B-Instruct`

## 为什么先测 1.5B

MiniMind v1/v2/v3 已经证明小模型在客服合规回复场景中存在生成质量和拒答稳定性限制。Qwen2.5-1.5B-Instruct 仍属于相对小的开源模型，但指令遵循和语言质量通常强于更小的实验模型，适合作为 v4 主线基座。

如果 1.5B 在本机显存或下载环境上不稳定，再退回 `Qwen/Qwen2.5-0.5B-Instruct`。

## 可能失败原因

- HuggingFace 下载网络问题
- 显存不足
- dtype 不兼容
- `device_map="auto"` 分配问题
- 本地 transformers / accelerate / torch 版本兼容问题

## 待填写：测试结果

## 测试结果

测试命令：

```powershell
C:\Users\20112\anaconda3\envs\minimind-lora\python.exe scripts/smoke_test_qwen_v4_model.py
```

运行环境：

- Python executable：`C:\Users\20112\anaconda3\envs\minimind-lora\python.exe`
- torch：`2.12.0.dev20260408+cu128`
- CUDA available：True
- GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU
- peft：available，0.19.1
- bitsandbytes：unavailable
- model：`Qwen/Qwen2.5-1.5B-Instruct`
- before load CUDA memory allocated：0.000 GB
- before load CUDA memory reserved：0.000 GB

结果：

- 模型下载/加载：失败
- tokenizer loaded：未成功
- model loaded：未成功
- 文本生成：未执行
- 显存占用：未进入模型加载阶段，仍为 0 GB 级别

失败原因：

HuggingFace 连接失败，本地缓存中也没有 `Qwen/Qwen2.5-1.5B-Instruct`。主要错误包括：

- `We couldn't connect to 'https://huggingface.co' to load the files`
- `couldn't find them in the cached files`
- `WinError 10013`
- `WinError 10051`
- DNS / network connection failure

脚本已分别尝试：

- `torch.bfloat16`
- `torch.float16`

但两次都失败在 HuggingFace 下载/读取模型配置阶段，尚未测试到显存是否足够，也尚未验证 dtype 是否兼容。

## 结论

本次 smoke test 没有完成 Qwen2.5-1.5B-Instruct 的下载、加载和生成。失败点是 HuggingFace 网络访问，不是显存不足或模型本身加载失败。

当前 Qwen LoRA 所需核心依赖中，`peft` 已可用；`bitsandbytes` 不可用，因此仍不建议优先走 4bit QLoRA。

暂不建议继续 Qwen baseline 100 条推理，因为本地尚未成功加载 Qwen 模型。

## ModelScope 本地路径尝试状态

已创建 ModelScope 下载脚本：

- `scripts/download_qwen_v4_modelscope.py`

目标本地路径：

- `models/qwen2_5_1_5b_instruct`

当前状态：

- `modelscope` 已安装
- 下载脚本已将 cache / credentials 路径改到项目内 `models/`
- ModelScope 网络访问仍失败，错误为 `WinError 10013`
- 本地模型目录不完整，缺少 `config.json`、`tokenizer_config.json`、`tokenizer.json`、`*.safetensors`
- 因此尚未运行本地路径 smoke test

## 建议下一步

可选方案：

1. 开启全局代理或配置 HuggingFace 可访问网络后重新运行 smoke test。
2. 使用 ModelScope 下载 Qwen2.5 模型到本地，再用本地路径运行 smoke test。
3. 如果 1.5B 下载或加载仍不顺利，先尝试 `Qwen/Qwen2.5-0.5B-Instruct` 做 smoke test。

注意：当前阶段仍不训练、不做 LoRA、不修改 MiniMind 源码。

## 本地模型 smoke test 成功更新

后续已通过本地模型路径完成 Qwen2.5-1.5B-Instruct smoke test：

- 本地路径：`models/qwen2_5_1_5b_instruct`
- dtype：bfloat16
- CUDA memory after load：2.875 GB allocated / 2.930 GB reserved
- CUDA memory after generation：2.907 GB allocated / 2.936 GB reserved
- 结果：成功生成客服回复
- 是否需要降级到 0.5B：不需要

建议继续进行 Qwen baseline 100 条 eval 推理。
