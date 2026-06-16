# v5 Real-Data Augmented Qwen LoRA Plan

## 为什么需要真实数据增强

v1-v4 已经完整跑通了从合成数据构造、MiniMind LoRA、系统化评估，到 Qwen2.5-1.5B LoRA 的实验链路。Qwen LoRA v4 在 rule-based rubric 上表现明显提升，但训练数据仍主要来自规则化合成样本。

下一阶段 v5 希望引入公开中文电商客服真实语料，让模型见到更多真实用户表达、真实客服话术和多轮上下文，从而提升回复自然度、表达多样性和真实业务场景覆盖。

## 当前模拟数据的局限

- 模板化：合成样本容易出现固定开头、固定结构和相似表达。
- 覆盖不足：真实用户会有错别字、口语、情绪化、省略信息和复杂混合诉求。
- 真实客服表达不足：模拟客服回复虽然合规，但可能不够自然，不够接近真实平台客服沟通。
- 业务分布偏窄：现有 hard cases 对拒答边界覆盖较好，但普通售后咨询、追问、上下文承接仍偏少。

## 真实数据的作用

- 增强用户问题的自然度和多样性。
- 学习真实客服的表达方式、问题确认方式和沟通节奏。
- 覆盖多轮对话中的追问、澄清、补充信息和情绪变化。
- 降低模型只记住合成模板的风险。

## 仍需保留模拟 Hard Cases

真实客服数据不一定包含足够多的合规拒答、平台规则边界和高风险诉求。因此 v5 不应直接用真实数据替代模拟数据，而应混合：

- 保留现有 synthetic compliance hard cases。
- 增加真实客服表达和真实用户说法。
- 对真实数据进行脱敏和质量过滤。
- 在训练后继续用 `data/eval_prompts_v3.jsonl` 检查拒答边界、不过度承诺和必要信息询问。

## 候选数据集

### JDDC / JDDC 2.1

JDDC / JDDC 2.1 是中文电商客服多轮对话相关公开语料，适合作为 v5 的主候选真实数据来源。它的价值在于包含真实用户和客服之间的自然表达、多轮上下文和电商售后/咨询场景。

计划用途：

- 从多轮对话中抽取 user -> assistant 单轮或相邻轮次 pair。
- 过滤过短、乱码、无效回复。
- 脱敏手机号、订单号、地址等潜在隐私信息。
- 转换为 Qwen `messages` SFT 格式。

### CSDS

CSDS 是中文客服对话摘要数据集，更适合摘要任务或对话理解任务。v5 暂不把它作为主训练数据，但后续可用于：

- 生成客服会话摘要能力扩展。
- 分析真实客服对话结构。
- 构造多任务或辅助评估样本。

## v5 数据混合策略

初始建议：

- synthetic compliance data：保留现有 v2/v4 合成合规数据，约 1000 条；Qwen v4 当前 train 为 800 条。
- real customer service extracted pairs：从 JDDC/JDDC 2.1 抽取 1000~3000 条。
- mixed Qwen SFT data：混合输出 `data/qwen_train_mixed_v5.jsonl`。

默认混合比例：

- synthetic：全部保留，用于保持合规规则、拒答边界和不过度承诺能力。
- real：先最多加入 2000 条，避免真实数据噪声压过合规 hard cases。
- shuffle seed：42。

## v5 训练策略

- base model：Qwen2.5-1.5B-Instruct local
- training method：PEFT LoRA
- epochs：1
- learning_rate：1e-4
- batch size：沿用 v4 的保守显存配置
- max_seq_length：512 起步
- 不使用 4bit QLoRA，除非后续 Windows 环境下 bitsandbytes 稳定可用

v5 的核心目标是增强自然度和多样性，不追求极低训练 loss。训练轮数和学习率应比 v4 更克制，避免进一步模板化或过拟合真实语料噪声。

## v5 评估策略

- 复用 `data/eval_prompts_v3.jsonl` 的 100 条统一评估集。
- 对比：
  - Qwen baseline
  - Qwen LoRA v4
  - Qwen real-data LoRA v5
- 复用 `scripts/evaluate_outputs_v3.py` 做 rule-based rubric 评分。
- 额外人工观察：
  - 回复是否更自然。
  - 是否减少固定模板开头。
  - 是否仍保留拒答边界。
  - 是否出现真实数据带来的不合规承诺或隐私泄漏风险。

## 风险和注意事项

- 数据许可：必须确认 JDDC/JDDC 2.1 的使用许可和引用要求。
- 隐私脱敏：手机号、订单号、地址、姓名等敏感信息必须清洗。
- 原始多轮格式复杂：真实数据可能包含 session、dialogue、turns 等不同结构，需要按实际字段适配转换脚本。
- 真实数据缺少合规拒答：公开客服语料可能偏普通问答，拒绝不合理请求样本不足，因此必须保留 synthetic hard cases。
- 数据噪声：真实客服回复可能不完整、过短、带内部标记或平台特定术语，需要过滤。

## 当前状态

- 已规划 v5 数据增强方案。
- 已准备真实数据检查脚本草案。
- 已准备 JDDC -> Qwen SFT 转换脚本草案。
- 已准备 synthetic + real 混合脚本。
- 已准备 mixed data 检查脚本。
- 暂未下载真实数据。
- 暂未训练 v5。
