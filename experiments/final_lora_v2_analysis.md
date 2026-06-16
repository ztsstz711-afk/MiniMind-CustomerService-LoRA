# Final LoRA v2 Analysis

## v2 数据与训练回顾

v2 数据集在 v1 的 300 条基础上扩展到 1000 条，训练划分为：

- train：800
- eval：200
- hard samples：557
- 重点增强：拒答边界、投诉安抚、退款/退货/发票/优惠券边界样本

LoRA v2 训练配置：

- base checkpoint：`minimind/out/full_sft_768.pth`
- LoRA adapter：`outputs/lora_customer_service_v2/lora_customer_service_v2_768.pth`
- hidden_size：768
- num_hidden_layers：8
- use_moe：0
- batch_size：4
- accumulation_steps：4
- epochs：3
- learning_rate：1e-4
- max_seq_len：340
- dtype：bfloat16
- GPU：NVIDIA GeForce RTX 5070 Ti Laptop GPU

## v1 vs v2 训练指标对比

| version | train/eval | first loss | last loss | adapter size |
| --- | ---: | ---: | ---: | ---: |
| v1 | 240 / 60 | 3.7383 | 2.8888 | 约 0.76 MB |
| v2 | 800 / 200 | 3.9860 | 2.2107 | 约 0.76 MB |

v2 的 loss 下降更明显，说明模型在更大的 v2 数据上继续拟合了客服回复风格。但 loss 只能证明训练过程有效，不能直接证明业务回复质量显著提升。

## 三方推理结果总结

本轮使用同一批 `data/baseline_prompts.jsonl`，共 10 条问题，对比：

- baseline：`outputs/baseline_outputs.jsonl`
- LoRA v1：`outputs/lora_outputs.jsonl`
- LoRA v2：`outputs/lora_v2_outputs.jsonl`

三方对比报告：

- `experiments/baseline_lora_v1_v2_comparison.md`
- `outputs/baseline_lora_v1_v2_comparison.jsonl`

自动关键词统计显示：

| 指标 | Baseline | LoRA v1 | LoRA v2 |
| --- | ---: | ---: | ---: |
| 礼貌开头 | 0 | 0 | 2 |
| 安抚表达 | 0 | 0 | 2 |
| 询问信息 | 7 | 7 | 6 |
| 规则说明 | 9 | 9 | 9 |
| 下一步操作 | 6 | 7 | 7 |
| 拒绝表达 | 3 | 0 | 1 |
| 空输出 | 0 | 0 | 0 |
| 过短输出 | 0 | 0 | 0 |
| 明显重复 | 0 | 2 | 1 |

## v2 是否改善

### 投诉安抚

有轻微改善。v2 在投诉安抚 case 中出现了“您好”等更像客服的开头，也更接近“先回应用户情绪，再给处理建议”的方向。

但改善有限。回复仍然偏泛化，方案不够贴近电商售后流程，缺少明确的订单号、售后单号、凭证、复核入口等关键信息。

### 拒绝不合理请求

没有稳定改善。对于“帮我编一个质量问题理由免运费退货”这类明确违规请求，v2 仍没有直接礼貌拒绝，反而继续生成了质量问题处理方案。这是 v2 当前最重要的失败点。

这说明即使 v2 增加了拒答边界样本，小模型仍可能在推理时被用户问题中的“质量问题/退货”语义带偏，没有稳定学到“不能协助虚构理由”的边界。

### 规则解释

规则解释数量上基本保持，但质量仍不稳定。v2 有时会提到规则、流程或需要核实，但表述容易泛化，不一定准确映射到真实电商售后规则。

### 询问必要信息

没有明显优于 v1。v2 在部分场景会要求提供订单号或信息，但也有一些 case 反而弱于 v1。说明数据增强还没有稳定转化为“必要信息询问”的行为模式。

### 回复稳定性

v2 没有空输出，也没有乱码。相比 v1，明显重复从 2 条降到 1 条，但仍存在重复、偏题、流程混乱的问题。例如退款进度 case 出现了较多“显示”的重复表达，订单取消和地址修改 case 仍然偏离真实售后流程。

## 主要不足

- MiniMind 小模型能力有限，对复杂业务边界的理解和泛化不足。
- v2 loss 下降明显，但生成效果没有同步大幅提升，不能只凭 loss 判断业务效果。
- 当前只有 10 条 prompt，属于初步人工评估，不足以代表整体能力。
- 自动评价规则主要基于关键词，只能做粗筛，不能替代人工评分。
- 拒绝不合理请求仍未稳定拒绝，是后续优化重点。
- 部分回复仍存在泛化、重复、偏题和事实流程不准确。

## 后续计划

- 构造 50~100 条 evaluation prompts，覆盖基础售后、hard cases、拒答边界和投诉升级。
- 加入自动评分 rubrics，例如礼貌安抚、规则解释、必要信息、下一步操作、拒答正确性、是否乱承诺。
- 对拒绝不合理请求构造更多 hard negative 样本，尤其是“表面像正常售后、实际要求违规”的问题。
- 尝试更明确的 system prompt 和 user prompt 格式，强化拒答边界。
- 迁移到 Qwen-0.5B / Qwen-1.5B 做 LoRA 对比，验证更强基座模型是否能更好吸收业务规则。

## 结论

LoRA v2 在训练指标上优于 v1，且在投诉安抚、礼貌开头等关键词维度有轻微改善。但从 10 条同题推理看，v2 尚未形成稳定的电商售后合规客服能力，尤其是在拒绝不合理请求上仍然失败。

这个结果是有价值的：它说明 v2 数据增强让训练更充分，但 MiniMind 小模型和当前数据规模仍不足以保证复杂业务边界稳定落地。下一阶段应扩大评估集，并迁移到 Qwen 小模型做对照实验。
