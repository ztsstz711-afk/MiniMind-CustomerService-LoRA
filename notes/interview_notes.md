# Interview Notes

## 项目一句话介绍

这是一个基于 MiniMind 的低资源电商售后合规回复 LoRA 微调实验，完整跑通了数据构造、格式转换、baseline 推理、LoRA 训练、LoRA 推理和 before/after 对比评估。

## 为什么选择 MiniMind

MiniMind 参数规模小，训练链路清晰，仓库提供了原生 PyTorch 训练、SFT、LoRA 和推理脚本，适合学习和复现实验。它不像大模型那样成本高，也不像黑盒 API 那样难以观察训练过程，因此适合做低资源微调闭环验证。

## 为什么用 LoRA

LoRA 只训练少量低秩增量参数，不更新完整模型权重。对小数据垂直场景来说，它更省显存、训练更快、adapter 体积更小。本项目的 LoRA adapter 约 0.76 MB，能直观看到参数高效微调的存储优势。

## SFT 数据格式是什么

原始 SFT 数据是 `instruction/input/output/category`。MiniMind 训练需要 `conversations` 格式，即多轮消息数组：

```json
{
  "conversations": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

训练时 MiniMind 的 Dataset 会用 tokenizer chat template 拼接对话，并 mask 掉 prompt，只对 assistant 回复计算 loss。

## LoRA 相比全量微调优势

- 显存占用更低。
- 训练速度更快。
- 只保存 adapter，文件很小。
- 可以为不同业务场景保存不同 adapter。
- 更适合低资源实验和快速验证。

## 为什么 loss 降了但效果提升有限

loss 下降说明模型在训练集上开始拟合回复分布，但不等于业务效果已经好。v1 数据只有 300 条左右，拒答边界样本少，模型本身也较小，所以它能学到一些表面风格，却没有稳定掌握售后规则和违规拒答边界。评估中也看到礼貌安抚和拒答能力提升不明显。

## 如果面试官说数据太少怎么回答

我会承认数据确实少。v1 的目标不是做线上可用客服，而是验证低资源 LoRA 的完整工程链路。数据少反而更能暴露小样本微调的局限。下一步会扩展到 1000+ 高质量样本，增加 hard cases、拒答边界、多轮追问和人工评估。

## 如果面试官说模型太小怎么回答

我会说这是刻意选择。MiniMind 小模型便于低成本复现训练和观察完整流程，但它不代表工业效果。小模型实验能快速验证数据格式、训练脚本、adapter 保存、推理对比等链路。后续会迁移到 Qwen-0.5B / Qwen-1.5B 做同样的数据和评估流程，比较模型容量带来的提升。

## 后续怎么升级到 Qwen

后续会把当前 `conversations` 数据转换成 Qwen chat template 兼容格式，使用 Qwen-0.5B / Qwen-1.5B 作为 base model，通过 PEFT 或 LLaMA-Factory 做 LoRA 微调。评估仍沿用同一批售后测试集和 before/after 维度，包括礼貌安抚、规则解释、必要信息、下一步操作和拒答边界。
