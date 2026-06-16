# Interview Notes

## 30 秒项目介绍

这是一个电商售后合规回复的低资源 LoRA 微调实验。我先用合成数据构造了售后客服 SFT 数据，覆盖物流、退款、退换货、发票、优惠券、投诉安抚和拒答边界等场景；然后用 MiniMind
跑通 baseline、LoRA 训练、推理和 before/after 对比。之后我发现小模型虽然能拟合风格，但合规拒答和复杂规则解释仍不稳定，所以迁移到
Qwen2.5-1.5B-Instruct，并用同一套 100 条 eval prompts 和 rule-based rubric 做横向评估。最终 Qwen LoRA v4 的自动评分从
Qwen baseline 的 6.275 提升到 7.865，但我也明确记录了 rule-based 评分和模板化风险的局限。

## 2 分钟项目介绍

项目分成五个阶段。v1 用 300 条模拟电商售后数据跑通 MiniMind LoRA 闭环，证明数据格式转换、训练、adapter 保存、推理和对比流程可行。v2 把数据扩展到 1000
条，重点增强拒绝不合理请求、投诉安抚和售后边界 hard cases。v3 构造 100 条统一评估 prompts，并实现 rule-based
rubric，从礼貌安抚、必要信息、规则说明、下一步操作、拒答、不安全承诺、重复和长度等维度评分。v4 迁移到 Qwen2.5-1.5B-Instruct，先做 baseline，再用同一套
800 条 Qwen 格式训练数据做 PEFT LoRA。结果上，MiniMind baseline 是 5.025，MiniMind LoRA v2 是 5.645，Qwen
baseline 是 6.275，Qwen LoRA v4 是 7.865。v5 目前只做真实数据增强规划，调研 JDDC/JDDC 2.1 和 CSDS，没有下载真实大数据，也没有训练。

## 项目一句话介绍

这是一个基于 MiniMind 的低资源电商售后合规回复 LoRA 微调实验，完整跑通了数据构造、格式转换、baseline 推理、LoRA 训练、LoRA 推理和 before/after
对比评估。

更完整地说，它已经从 MiniMind 小模型实验扩展到 Qwen2.5-1.5B 迁移实验，并加入了统一 100 条 eval prompts 和 rule-based rubric
自动评分。

## 为什么选择 MiniMind

MiniMind 参数规模小，训练链路清晰，仓库提供了原生 PyTorch 训练、SFT、LoRA 和推理脚本，适合学习和复现实验。它不像大模型那样成本高，也不像黑盒 API
那样难以观察训练过程，因此适合做低资源微调闭环验证。

## 为什么用 LoRA

LoRA 只训练少量低秩增量参数，不更新完整模型权重。对小数据垂直场景来说，它更省显存、训练更快、adapter 体积更小。本项目的 LoRA adapter 约 0.76
MB，能直观看到参数高效微调的存储优势。

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

loss 下降说明模型在训练集上开始拟合回复分布，但不等于业务效果已经好。v1 数据只有 300 条左右，拒答边界样本少，模型本身也较小，所以它能学到一些表面风格，却没有稳定掌握售后规则和违规
拒答边界。评估中也看到礼貌安抚和拒答能力提升不明显。

## 如果面试官说数据太少怎么回答

我会承认数据确实少。v1 的目标不是做线上可用客服，而是验证低资源 LoRA 的完整工程链路。数据少反而更能暴露小样本微调的局限。下一步会扩展到 1000+ 高质量样本，增加 hard
cases、拒答边界、多轮追问和人工评估。

## 如果面试官说模型太小怎么回答

我会说这是刻意选择。MiniMind 小模型便于低成本复现训练和观察完整流程，但它不代表工业效果。小模型实验能快速验证数据格式、训练脚本、adapter 保存、推理对比等链路。后续会迁移到
Qwen-0.5B / Qwen-1.5B 做同样的数据和评估流程，比较模型容量带来的提升。

## 后续怎么升级到 Qwen

后续会把当前 `conversations` 数据转换成 Qwen chat template 兼容格式，使用 Qwen-0.5B / Qwen-1.5B 作为 base model，通过
PEFT 或 LLaMA-Factory 做 LoRA 微调。评估仍沿用同一批售后测试集和 before/after 维度，包括礼貌安抚、规则解释、必要信息、下一步操作和拒答边界。

这个升级已经完成到 Qwen2.5-1.5B-Instruct：Qwen baseline 在 100 条 eval prompts 上 overall score 为 6.275，Qwen
LoRA v4 为 7.865，说明更强基座模型加少量垂直合规数据能显著提升 rule-based 指标。

## MiniMind 线怎么讲

MiniMind 线的重点不是追求最高效果，而是低成本跑通训练闭环。
它展示了我如何读上游仓库、确认 Dataset 格式、把 `instruction/input/output/category` 转成 `conversations`，
再做 baseline 推理、LoRA 训练、LoRA 推理和对比评估。

可以这样讲：MiniMind v1/v2 证明了低资源 LoRA 流程可复现，但也暴露了小模型限制。MiniMind LoRA v2 从 baseline 的 5.025 提升到
5.645，有提升但不够强，拒答和复杂售后规则仍不稳定。这给了我迁移 Qwen 的技术动机。

## Qwen 线怎么讲

Qwen 线的重点是验证更强基座模型的价值。我把 v2 数据转换成 Qwen messages 格式，用 Qwen2.5-1.5B-Instruct 做 baseline，再进行 PEFT
LoRA。Qwen baseline 已经达到 6.275，超过 MiniMind LoRA v2 的 5.645。完成 Qwen LoRA v4 后 overall score 到
7.865，拒绝不合理请求类平均分到 8.500，unsafe flags 为 0。

这条线说明：模型容量和预训练/指令能力非常关键。LoRA 不是魔法，它更像是在强基座上注入垂直场景风格和规则流程。

## 为什么 Qwen baseline 比 MiniMind LoRA 强

因为 Qwen2.5-1.5B-Instruct 的基座能力、指令跟随能力和通用客服表达能力明显强于 MiniMind 小模型。即使 MiniMind 做了
LoRA，它能学习到的更多是表层客服风格；但复杂规则解释、长文本组织、拒答边界和自然语言表达依赖模型本身的能力上限。

所以这个项目里一个重要结论是：数据和 LoRA 很重要，但基座模型能力同样关键。强基座 baseline 可能直接超过弱基座 LoRA。

## 为什么 LoRA 后分数提升不代表线上一定可用

因为训练和评估都发生在有限数据和有限测试集上。LoRA 后分数提升说明模型在这套 rule-based rubric 下更常命中礼貌、规则、必要信息、下一步和拒答等关键词，但真实线上客服还涉及
更多问题：

- 是否真正理解用户上下文。
- 是否给出正确平台规则。
- 是否避免隐含承诺。
- 是否处理多轮追问。
- 是否稳定拒绝灰色请求。
- 是否符合具体平台的真实售后政策。

因此我会把它表述为“离线实验指标提升”，不是“线上客服可用”。

## 为什么 rule-based evaluation 有局限

rule-based evaluation 的好处是可复现、成本低、能快速横向比较。但它有明显局限：

- 关键词命中不等于真实理解。
- 可能奖励模板化话术。
- 难以判断规则解释是否事实正确。
- 难以判断拒答是否既明确又给了合规替代方案。
- 难以识别语气、上下文承接和业务细节错误。

所以我在 README 和总结里明确写了：rule-based evaluation 不能等同于人工业务评估。下一步应该加入人工评分或 LLM-as-a-judge。

## 为什么 v5 真实数据没有继续做

v5 的目标是引入 JDDC/JDDC 2.1 或 CSDS 这类真实中文客服语料，增强真实用户表达和客服回复自然度。但当前只做了数据源探测，没有下载大数据、没有训练，原因是：

- JDDC 2.1 GitHub 只有申请入口，没有直接 sample/dev/test 小文件。
- 多模态数据可能很大，不适合直接下载完整包。
- 真实客服数据涉及许可和隐私脱敏风险。
- 真实数据不一定包含足够的合规拒答 hard cases，不能直接替代合成合规数据。

所以 v5 的正确下一步是先申请或下载小规模文本-only sample，检查格式和许可，再抽取 1000~3000 条 user-agent pair，与现有 synthetic hard
cases 混合。

## 项目局限和下一步优化

主要局限：

- 合成数据仍然偏模板化。
- 100 条 eval prompts 规模不大。
- rule-based rubric 不能替代人工判断。
- 真实业务规则没有接入真实平台政策库。
- 当前主要是单轮回复，缺少多轮对话训练。
- Qwen LoRA v4 分数提升明显，但部分开头话术集中，可能有模板化倾向。

下一步优化：

- 引入真实客服文本数据，但保留合规 hard cases。
- 构造 300~500 条更细的 eval prompts。
- 加入人工评分或 LLM-as-a-judge。
- 做 Qwen LoRA ablation，例如 epochs=1、learning_rate=1e-4。
- 尝试 Qwen2.5-3B baseline / LoRA。
- 将拒答边界拆成更细的安全策略标签。

## 面试追问与回答要点

### 1. 这个项目和线上客服系统有什么区别？

这是离线 LoRA 微调和评估实验，不是线上客服系统。它没有接入订单系统、物流系统、实时政策库和人工审核流程，也没有做线上安全测试。

### 2. 为什么选电商售后？

因为规则清晰、场景可控，适合验证模型是否能礼貌安抚、解释规则、询问信息、给出下一步，并拒绝不合理请求。

### 3. 数据是怎么来的？

v1/v2 是我构造的合成合规 SFT 数据，覆盖 10 类售后场景。v5 规划引入真实数据，但目前还没有下载真实大数据，也没有训练。

### 4. 为什么不用真实数据直接训练？

真实数据有许可、隐私脱敏、格式复杂和质量噪声问题，而且真实客服语料不一定包含足够拒答边界样本。所以我先用合成 hard cases 保证合规边界，再规划真实数据增强自然度。

### 5. MiniMind 的价值是什么？

MiniMind 让训练链路足够轻，适合低成本理解 SFT/LoRA 数据格式、训练入口、adapter 保存和推理过程。它是工程闭环验证的起点。

### 6. MiniMind 的限制是什么？

模型能力有限，复杂售后规则、拒答稳定性和自然表达都不够好。v3 评分里 MiniMind LoRA v2 只有 5.645，说明提升有限。

### 7. Qwen 为什么提升明显？

Qwen2.5-1.5B-Instruct 本身指令跟随和语言组织能力更强。Qwen baseline 6.275 已超过 MiniMind LoRA v2，说明基座模型能力很重要。

### 8. Qwen LoRA 学到了什么？

它更稳定地输出客服流程元素，比如礼貌开头、必要信息、规则说明、下一步操作和拒答表达。Qwen LoRA v4 overall score 到 7.865。

### 9. loss 从 4.038 降到 0.084 是否说明模型很好？

不能。低 loss 说明训练集拟合强，但也可能意味着过拟合或模板化。必须看独立 eval prompts、输出质量和人工评估。

### 10. 为什么不用 accuracy？

客服回复是生成任务，没有唯一标准答案。更适合用 rubric 评估结构和合规要素，再结合人工判断。

### 11. rule-based rubric 怎么设计的？

按客服回复需要的要素设计：礼貌安抚、必要信息、规则说明、下一步操作、拒答表达、不安全承诺惩罚、重复惩罚和长度惩罚。

### 12. rule-based rubric 最大问题是什么？

它依赖关键词，可能把模板化回答评高，也无法判断规则是否真正正确。因此只能做粗评。

### 13. 为什么 Qwen LoRA 可能模板化？

训练数据是合成客服数据，结构和话术比较一致。LoRA 学到稳定风格的同时，也可能放大固定开头和固定流程。

### 14. 如果重新做，你会怎么改数据？

我会加入真实用户表达、更多多轮追问、更多边界案例，并把拒答样本拆成更细标签，例如隐私、赔偿、发票、售后期、伪造信息等。

### 15. 如果面试官质疑分数，你怎么回应？

我会承认分数只是 rule-based 粗评，不等同于业务质量。项目价值在于完整实验链路、可复现评估和诚实记录局限，而不是夸大模型效果。

### 16. 为什么 adapter 大小也值得讲？

它体现参数高效微调。MiniMind adapter 约 0.76 MB，Qwen LoRA adapter 约 35.27 MB，相比完整模型小很多，适合保存多个业务场景 adapter。

### 17. 这个项目最能体现你的什么能力？

能体现我从业务场景出发设计数据，读懂开源训练代码，完成格式转换、训练、推理、评估、结果分析和展示整理的端到端工程能力。

### 18. 下一步最有价值的改进是什么？

引入真实客服文本数据，做人工/LLM-as-a-judge 评估，并对 Qwen LoRA 的训练轮数和学习率做 ablation，确认提升不是过拟合。
