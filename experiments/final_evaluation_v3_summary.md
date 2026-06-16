# Final Evaluation v3 Summary

## v3 评估目标

v3 的目标是把此前 10 条 prompt 的人工观察，升级为 100 条 evaluation prompts + rule-based rubric 的系统化自动评估。评估对象包括：

- baseline
- LoRA v1
- LoRA v2

本阶段不训练、不下载权重、不修改 MiniMind 源码，只对已有 100 条推理输出做统一评分。

## 100 条 Eval Prompts 设计

评估集文件：

- `data/eval_prompts_v3.jsonl`

规模与结构：

- 总数：100
- 10 类售后场景，每类 10 条
- difficulty 分布：easy 13 / medium 38 / hard 49
- 每条包含：`id`、`category`、`prompt`、`expected_behavior`、`required_elements`、`forbidden_elements`、`difficulty`、`tags`

重点覆盖：

- 拒绝不合理请求
- 投诉安抚
- 退款/退货/发票/优惠券边界场景
- 不应乱承诺、不应绕过平台规则、不应帮助伪造理由的 hard cases

## 三模型输出检查结果

| model | rows | empty | very short | repeated tendency | garbled |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 100 | 0 | 0 | 2 | 2 |
| LoRA v1 | 100 | 0 | 0 | 8 | 1 |
| LoRA v2 | 100 | 0 | 0 | 6 | 1 |

三组输出都已通过结构检查。疑似乱码主要是生成文本中出现 `�` 替换字符，属于模型生成质量问题，不是 JSONL 写入或对齐错误。

## 自动评分结果摘要

| model | overall avg | hard avg | refusal avg | refusal present | unsafe flags | repetition penalty |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 5.025 | 5.510 | 6.350 | 3/10 | 0 | 2.0 |
| LoRA v1 | 5.375 | 6.010 | 6.850 | 5/10 | 0 | 8.0 |
| LoRA v2 | 5.645 | 6.347 | 7.450 | 3/10 | 0 | 6.0 |

整体平均分：

- LoRA v1 - baseline：+0.350
- LoRA v2 - LoRA v1：+0.270
- LoRA v2 - baseline：+0.620

从 rule-based rubric 看，LoRA v2 的整体平均分最高，hard cases 平均分最高，拒绝不合理请求类别平均分也最高。

## Category-Level 结果

| category | baseline | LoRA v1 | LoRA v2 | best |
| --- | ---: | ---: | ---: | --- |
| 优惠券使用 | 4.450 | 5.050 | 6.550 | LoRA v2 |
| 发票开具 | 4.650 | 4.950 | 4.900 | LoRA v1 |
| 商品咨询 | 3.750 | 3.450 | 3.500 | baseline |
| 地址修改 | 5.050 | 5.800 | 4.550 | LoRA v1 |
| 投诉安抚 | 4.700 | 5.750 | 6.150 | LoRA v2 |
| 拒绝不合理请求 | 6.350 | 6.850 | 7.450 | LoRA v2 |
| 物流查询 | 5.300 | 5.200 | 5.100 | baseline |
| 订单取消 | 5.200 | 5.250 | 5.700 | LoRA v2 |
| 退换货申请 | 4.200 | 5.900 | 6.200 | LoRA v2 |
| 退款进度 | 6.600 | 5.550 | 6.350 | baseline |

LoRA v2 在优惠券使用、投诉安抚、拒绝不合理请求、订单取消、退换货申请等类别上取得最高规则分。baseline 在商品咨询、物流查询、退款进度上仍然更高，说明 LoRA 并非全面提升。

## Hard Cases 结果

hard 平均分：

- baseline：5.510
- LoRA v1：6.010
- LoRA v2：6.347

v2 在 hard cases 上的规则分最高，说明 v2 数据中增加的 hard cases 和拒答边界样本，在关键词维度上产生了一定影响。

## 拒绝不合理请求类结果

拒绝不合理请求类别平均分：

- baseline：6.350
- LoRA v1：6.850
- LoRA v2：7.450

但需要谨慎解释：`refusal_present` 计数为：

- baseline：3/10
- LoRA v1：5/10
- LoRA v2：3/10

也就是说，v2 虽然在该类别总分更高，但并没有在“明确拒绝词出现次数”上优于 v1。v2 的得分提升可能来自规则说明、下一步操作、礼貌表达等维度，而不是稳定拒答能力真正建立。

## v2 是否真的优于 v1

从 rule-based 总分看，v2 优于 v1：

- overall：5.645 vs 5.375
- hard：6.347 vs 6.010
- refusal category avg：7.450 vs 6.850

但从生成质量风险看，v2 并没有形成压倒性优势：

- v2 仍有 6 条重复倾向输出。
- v2 仍有 1 条疑似乱码输出。
- v2 的拒绝词命中为 3/10，低于 v1 的 5/10。
- rule-based 评分会偏向关键词命中，不能确认语义上真的合规。

结论：v2 在自动规则评分上有可见提升，但不能说“明显更好”或“业务可用”。更准确的说法是：v2 比 v1 更像朝目标方向移动了一步，但拒答稳定性和真实业务质量仍需要人工评估或 LLM-as-a-judge 验证。

## 局限

- rule-based 评分有偏差，只能做粗粒度趋势筛查。
- 小模型生成不稳定，容易重复、泛化或偏题。
- 合规拒答仍然是主要短板。
- 关键词命中不代表规则理解正确。
- 100 条 eval prompts 比 10 条更稳，但仍不是工业级评测集。
- 需要人工评估或 LLM-as-a-judge 辅助确认真实质量。

## 后续 v4

- 迁移到 Qwen-0.5B / Qwen-1.5B。
- 用同一套 100 条 eval prompts 对比更强基座模型。
- 继续复用 rule-based rubric，同时增加人工评分或 LLM-as-a-judge。
- 重点观察拒答边界、投诉安抚、必要信息询问和下一步操作是否更稳定。
- 对 hard cases 做更细粒度失败分析，反向优化训练数据。
