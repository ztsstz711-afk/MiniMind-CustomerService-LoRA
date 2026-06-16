# Evaluation v3 Plan

## 为什么 v3 要做系统化评估

v1 和 v2 已经跑通了数据构造、MiniMind baseline、LoRA 训练、LoRA 推理和 before/after 对比。但目前主要依赖 10 条固定 prompts 做人工观察，样本量太小，无法稳定判断模型在不同售后场景中的真实变化。

v3 的目标是建立一个更系统的评估层：用 100 条固定 evaluation prompts 覆盖 10 类售后场景，再用 rule-based rubric 对 baseline / LoRA v1 / LoRA v2 的输出做统一自动评分。

## v1/v2 10 条 prompt 的局限

- 每类只有 1 条问题，覆盖面太窄。
- 对拒答边界、投诉安抚、退款/退货/发票/优惠券边界样本覆盖不足。
- 单条输出容易受采样随机性影响。
- 无法形成 category-level 或 difficulty-level 的稳定对比。
- 人工观察有价值，但难以快速复现和量化。

## v3 100 条评估集设计

评估集文件：

- `data/eval_prompts_v3.jsonl`

字段：

- `id`
- `category`
- `prompt`
- `expected_behavior`
- `required_elements`
- `forbidden_elements`
- `difficulty`
- `tags`

类别保持 10 类，每类 10 条：

- 物流查询
- 退款进度
- 退换货申请
- 发票开具
- 优惠券使用
- 商品咨询
- 订单取消
- 投诉安抚
- 拒绝不合理请求
- 地址修改

设计重点：

- `拒绝不合理请求` 全部为 hard。
- `投诉安抚` 至少 7 条为 hard。
- 退款、退货、发票、优惠券包含边界场景。
- 每条 prompt 都标注期望行为、必备元素和禁止元素。

## Rubric 评分维度

评分脚本：

- `scripts/evaluate_outputs_v3.py`

主要维度：

- `politeness_score`：是否包含“您好/亲/抱歉/理解/感谢”等礼貌或安抚表达。
- `info_request_score`：是否询问订单号、手机号后四位、商品信息、物流单号等必要信息。
- `policy_score`：是否包含规则、平台、售后期、审核、核实、不支持、不符合等规则说明。
- `next_step_score`：是否给出下一步操作，例如提供订单号、提交申请、等待审核、联系客服。
- `refusal_score`：重点用于拒绝不合理请求类，检查是否包含不能/无法/不支持/不符合规则/无法协助等拒绝表达。
- `unsafe_promise_penalty`：如果出现一定退款、保证赔偿、绕过平台、帮你编、可以免审核等，扣分。
- `repetition_penalty`：输出重复严重时扣分。
- `length_penalty`：输出过短或过长时扣分。

总分：

- `total_score` 满分 10。
- 同时输出各项分数和 flags。

## 评分局限

rule-based rubric 只能做粗评，不能代替人工判断。它能稳定发现一些明显问题，例如缺少拒答、缺少必要信息、出现危险承诺或严重重复，但无法完整判断语义是否真正合规、规则是否准确、措辞是否自然。

因此 v3 的自动评分应作为筛查工具，而不是最终业务结论。后续仍需要人工评分或 LLM-as-Judge 做交叉验证。

## 后续计划

1. 使用 `data/eval_prompts_v3.jsonl` 对 baseline 生成 100 条输出。
2. 使用同一批 prompts 对 LoRA v1 生成 100 条输出。
3. 使用同一批 prompts 对 LoRA v2 生成 100 条输出。
4. 分别运行 `scripts/evaluate_outputs_v3.py` 输出评分报告。
5. 汇总 baseline / LoRA v1 / LoRA v2 的 category-level、difficulty-level 和 refusal performance。
6. 根据失败 case 继续优化数据集，或迁移到 Qwen-0.5B / Qwen-1.5B 做 LoRA 对比。
