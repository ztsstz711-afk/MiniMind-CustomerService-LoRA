# Dataset v2 Summary

## v2 数据目标

v2 的目标是在不训练、不修改 MiniMind 上游源码的前提下，将 v1 的 300 条电商售后客服 SFT 数据扩展到约 1000 条，并重点增强 hard cases 和拒答边界样本。

输出文件：

- `data/customer_service_sft_v2.jsonl`
- `data/train_v2.jsonl`
- `data/eval_v2.jsonl`
- `data/minimind_train_v2.jsonl`
- `data/minimind_eval_v2.jsonl`

## 总样本数

- 总样本数：1000
- train_v2：800
- eval_v2：200

## 类别分布

| category | count |
| --- | ---: |
| 物流查询 | 90 |
| 退款进度 | 90 |
| 退换货申请 | 90 |
| 发票开具 | 90 |
| 优惠券使用 | 90 |
| 商品咨询 | 90 |
| 订单取消 | 90 |
| 投诉安抚 | 120 |
| 拒绝不合理请求 | 160 |
| 地址修改 | 90 |

## difficulty 分布

| difficulty | count |
| --- | ---: |
| easy | 112 |
| medium | 331 |
| hard | 557 |

## hard cases 设计

v2 重点增强了两类高风险样本：

- 拒绝不合理请求：160 条，覆盖过期优惠券恢复、发票多开、不退货直接退款、已使用商品按全新退、索要他人订单信息、索要商家私人联系方式、超出售后期强制退货、威胁差评要求赔偿、伪造物流/售后状态、要求客服绕过平台规则等。
- 投诉安抚：120 条，覆盖用户情绪激烈、多次催促、威胁投诉、质疑欺骗、对客服不信任、要求明确处理时限等。

退款、退货、发票、优惠券等类别也加入了更多边界问题，例如部分退款争议、已使用商品退货、虚开发票、过期优惠券恢复和优惠券提现等。

## 相比 v1 的改进

- 数据规模从 300 条扩展到 1000 条。
- 新增 `difficulty` 字段，用于区分 easy / medium / hard。
- 新增 `tags` 字段，便于后续筛选 hard cases、拒答样本和业务子场景。
- 增强拒答边界，不再只覆盖普通售后问题。
- 投诉安抚类样本数量提升，并要求回复包含明确安抚表达。
- 输出模板改为多模板随机组合，降低同类回复完全模板化的风险。
- 已生成 MiniMind `conversations` v2 格式，可直接进入后续 LoRA 训练准备。

## 数据检查结果

`scripts/check_dataset_v2.py` 已通过，检查项包括：

- 总样本数
- 类别分布
- difficulty 分布
- tags 分布
- 必需字段完整性
- 空 input / output
- 重复 input + output
- 输出长度统计
- 拒绝类回复的拒绝表达
- 投诉类回复的安抚表达

输出长度统计：

- min：86
- avg：123.5
- max：175

重复 `input + output`：0。

## 后续训练计划

下一阶段可以基于 v2 数据重新运行 LoRA 微调，并与 v1 LoRA 结果对比：

- v1 300 条 vs v2 1000 条
- loss 曲线差异
- 拒答边界改善情况
- 投诉安抚稳定性
- before/after 输出质量
- MiniMind v2 LoRA 与后续 Qwen 小模型 LoRA 的效果对比
