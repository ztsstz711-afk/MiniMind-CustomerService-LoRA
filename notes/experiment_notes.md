# Experiment Notes

## Experiment Summary

这是一个电商售后合规回复的低资源 LoRA 微调实验。

我先构造合成客服 SFT 数据，用 MiniMind 跑通 baseline、LoRA 训练、推理和对比。

然后我发现小模型虽然能拟合客服风格，但拒答边界和复杂规则解释仍不稳定。

所以我迁移到 Qwen2.5-1.5B-Instruct。

在同一套 100 条 eval prompts 和 rule-based rubric 下，Qwen baseline 得分 6.275。

Qwen LoRA v4 得分 7.865。

但我也明确说明，自动评分不能等同于人工业务评估。

## Experiment Details

项目分为五个阶段。

v1 用 300 条合成电商售后数据跑通 MiniMind LoRA 闭环。

这个阶段主要验证数据构造、格式转换、训练、adapter 保存、推理和 before/after 对比。

v2 把数据扩展到 1000 条。

v2 重点增强拒绝不合理请求、投诉安抚、退款退货边界和发票优惠券边界样本。

v3 构造 100 条统一 eval prompts。

v3 实现 rule-based rubric，从礼貌安抚、必要信息、规则说明、下一步操作、拒答、不安全承诺、重复和长度等维度评分。

v4 迁移到 Qwen2.5-1.5B-Instruct。

Qwen baseline 已经超过 MiniMind LoRA v2。

Qwen LoRA v4 在统一自动评分下进一步提升到 7.865。

v5 目前只是规划和数据源探测阶段。

它计划引入 JDDC、JDDC 2.1 或 CSDS 这类真实客服数据，但没有下载真实大数据，也没有训练。

## Short Summary

这是一个从 MiniMind 到 Qwen2.5 的电商售后合规回复 LoRA 微调实验。

它完整覆盖数据构造、格式转换、训练、推理、自动评估和结果分析。

## 为什么选择电商售后

电商售后规则相对明确。

模型需要礼貌安抚用户。

模型需要解释平台规则。

模型需要询问订单号、截图、物流单号等必要信息。

模型需要给出下一步操作。

模型不能乱承诺。

模型需要拒绝违规或不合理请求。

所以这个场景很适合验证 SFT / LoRA 是否真的改善合规回复。

## MiniMind Track

MiniMind 线的价值是低成本跑通完整微调流程。

MiniMind 小模型训练链路清晰。

它适合用来学习 SFT 数据格式、LoRA 训练入口、Dataset 处理逻辑和推理流程。

我把原始 `instruction/input/output/category` 数据转换成 MiniMind 的 `conversations` 格式。

然后完成 baseline 推理、LoRA v1、LoRA v2 和三方对比。

MiniMind baseline 得分 5.025。

MiniMind LoRA v1 得分 5.375。

MiniMind LoRA v2 得分 5.645。

这说明 LoRA 有提升。

但提升不大。

它也暴露了小模型能力边界。

## Qwen Track

Qwen 线的价值是验证更强基座模型。

我把 v2 数据转换成 Qwen messages 格式。

我先做 Qwen2.5-1.5B-Instruct baseline。

Qwen baseline 得分 6.275。

这已经超过 MiniMind LoRA v2。

然后我用 800 条 Qwen 格式训练数据做 PEFT LoRA。

Qwen LoRA v4 得分 7.865。

Qwen LoRA v4 拒绝不合理请求类平均分为 8.500。

Qwen LoRA v4 unsafe flags 为 0。

## 为什么 Qwen baseline 比 MiniMind LoRA 强

因为 Qwen2.5-1.5B-Instruct 的基座能力更强。

它有更好的指令跟随能力。

它有更好的语言组织能力。

它对客服类任务的通用表达也更自然。

MiniMind LoRA 能学到一些垂直风格。

但小模型容量限制了复杂规则理解和稳定拒答能力。

所以强基座 baseline 可能直接超过弱基座 LoRA。

## 为什么 LoRA 后分数提升不代表线上一定可用

LoRA 后分数提升说明模型在离线评估中更常命中 rubric 要素。

但线上客服需要更多能力。

它需要接入真实订单状态。

它需要遵守具体平台政策。

它需要处理多轮上下文。

它需要在高风险问题上稳定拒答。

它还需要人工审核和安全兜底。

所以这个项目只应被描述为离线微调实验。

## 为什么 rule-based evaluation 有局限

rule-based evaluation 的优点是便宜、稳定、可复现。

它适合横向比较模型。

但它依赖关键词和简单规则。

关键词命中不代表真正理解。

固定客服话术可能让分数变高。

它无法判断规则解释是否事实正确。

它无法完全判断拒答是否合规。

所以还需要人工评估或 LLM-as-a-judge。

## 为什么 v5 真实数据没有继续训练

v5 的目标是引入真实中文电商客服语料。

候选数据包括 JDDC、JDDC 2.1 和 CSDS。

但 JDDC 2.1 GitHub 主要是申请入口。

它没有直接提供 sample、dev 或 text-only 小文件。

完整多模态数据可能很大。

真实数据还涉及许可和隐私脱敏。

所以当前只做规划和数据源探测。

没有下载真实大数据。

没有训练 v5。

## 项目局限

合成数据仍可能模板化。

评估集只有 100 条。

rule-based rubric 不能替代人工判断。

当前主要是单轮回复。

没有接入真实订单系统。

没有接入真实平台政策库。

Qwen LoRA v4 虽然分数高，但可能存在固定话术集中。

## 下一步优化

引入真实客服文本数据。

保留合成 hard cases。

扩展 evaluation prompts。

加入人工评分。

加入 LLM-as-a-judge。

做 Qwen LoRA ablation。

尝试 Qwen2.5-3B baseline 和 LoRA。

## Common Questions

### 1. 这个项目是不是线上客服系统？

不是。

它是离线 SFT / LoRA 微调和评估实验。

它没有接入订单系统、物流系统、政策库和人工审核流程。

### 2. 为什么选择 LoRA？

LoRA 只训练少量增量参数。

它显存占用低。

它训练更快。

它只需要保存 adapter。

它适合低资源垂直场景验证。

### 3. SFT 数据格式是什么？

原始数据是 `instruction/input/output/category`。

MiniMind 使用 `conversations` 格式。

Qwen 使用 `messages` 格式。

二者都包含 system、user 和 assistant 消息。

### 4. 为什么要做 baseline？

没有 baseline 就无法判断 LoRA 是否真的改善。

baseline 可以展示模型微调前的原始表现。

before/after 对比是这个项目的核心证据之一。

### 5. 为什么 MiniMind 效果有限？

MiniMind 模型小。

它更容易学习表层风格。

但复杂规则解释和拒答稳定性需要更强模型能力。

### 6. 为什么 Qwen 提升明显？

Qwen2.5-1.5B-Instruct 本身能力更强。

LoRA 进一步把它引导到电商售后合规场景。

### 7. loss 很低是否说明模型很好？

不一定。

低 loss 可能意味着拟合训练集。

也可能意味着过拟合。

必须看独立评估集和人工质量。

### 8. Qwen LoRA v4 有没有模板化风险？

有可能。

部分输出开头比较集中。

这也是为什么我强调 rule-based score 不能替代人工评估。

### 9. 为什么不用真实数据直接训练？

真实数据有许可风险。

真实数据需要脱敏。

真实数据格式复杂。

真实数据可能缺少合规拒答 hard cases。

所以要先做小样本探测和清洗。

### 10. v5 会怎么做？

优先申请或下载 text-only 小样本。

先检查字段和许可。

再抽取 1000 到 3000 条 user-agent pair。

最后和 synthetic hard cases 混合训练。

### 11. 自动评分怎么设计？

它检查礼貌、必要信息、规则说明、下一步、拒答、不安全承诺、重复和长度。

每个维度用关键词或简单规则实现。

### 12. 自动评分最大问题是什么？

它不能判断真实业务正确性。

它可能奖励模板化表达。

它不能完全识别隐含承诺。

### 13. 这个项目最有价值的地方是什么？

它不是只跑一个训练命令。

它完整覆盖数据、训练、推理、评估、对比和总结。

它也诚实记录失败和局限。

### 14. 如果要上线还缺什么？

缺真实业务系统接入。

缺人工审核。

缺安全策略。

缺真实政策库。

缺大规模人工评估。

### 15. 为什么 adapter size 值得讲？

它体现参数高效微调。

MiniMind adapter 约 0.76 MB。

Qwen LoRA adapter 约 35.27 MB。

这比保存完整模型轻很多。

### 16. 项目如何扩展？

扩展真实数据。

扩展评估集。

换更强基座模型。

做 ablation。

加入 LLM-as-a-judge。

### 17. 如果 project review 质疑数据是合成的怎么办？

我会承认这是限制。

我会说明合成数据用于控制合规边界。

下一步会用真实数据增强自然度。

但真实数据不能替代 hard cases。

### 18. 如果 engineering discussion 质疑评分不可靠怎么办？

我会同意。

rule-based 评分只是第一层自动筛查。

真实业务质量需要人工评估和更强 judge。

### 19. 最重要的实验结论是什么？

更强基座模型非常关键。

MiniMind LoRA 能跑通流程但效果有限。

Qwen baseline 已超过 MiniMind LoRA v2。

Qwen LoRA v4 在统一自动评分下表现最好。

### 20. 这个项目体现了什么能力？

业务场景拆解。

数据构造。

开源训练代码阅读。

LoRA 微调。

推理脚本编写。

自动评估。

结果分析。

项目文档整理。
