# V1 vs V2 LoRA Training Comparison

## 数据规模

| version | train | eval | data focus |
| --- | ---: | ---: | --- |
| v1 | 240 | 60 | 10 类售后基础场景，完成 LoRA 闭环验证 |
| v2 | 800 | 200 | 增强 hard cases、拒答边界、投诉安抚和售后边界样本 |

## 训练配置

v1 和 v2 均基于同一个 MiniMind base checkpoint：

- base checkpoint：`minimind/out/full_sft_768.pth`
- hidden_size：768
- num_hidden_layers：8
- use_moe：0
- batch_size：4
- accumulation_steps：4
- epochs：3
- learning_rate：1e-4
- max_seq_len：340
- dtype：bfloat16
- device：cuda:0

## Loss 对比

| version | first loss | last loss | loss logs |
| --- | ---: | ---: | ---: |
| v1 | 3.7383 | 2.8888 | 12 |
| v2 | 3.9860 | 2.2107 | 60 |

v2 数据量更大，训练 step 更多，loss 从 3.9860 降到 2.2107，说明模型继续拟合了 v2 数据中的客服回复风格和更密集的 hard cases。

## Adapter Size

| version | adapter path | size |
| --- | --- | ---: |
| v1 | `outputs/lora_customer_service/lora_customer_service_768.pth` | 约 0.76 MB |
| v2 | `outputs/lora_customer_service_v2/lora_customer_service_v2_768.pth` | 798177 bytes，约 0.76 MB |

两版 adapter 大小基本一致，符合 LoRA 参数量由模型结构和 LoRA 注入位置决定，而不是由数据量直接决定的预期。

## 检查结论

- v2 训练已成功完成。
- v2 stdout 中 loss 正常出现，未发现 NaN / inf。
- v2 stderr 无 Traceback、Error、CUDA out of memory 或 checkpoint mismatch。
- v2 stderr 仅包含 datasets 生成 train split 的进度输出。

## 对比结论

v2 使用了更多训练数据，尤其强化了 hard cases 和拒答边界样本。loss 下降幅度比 v1 更明显，但这只能说明训练过程和数据拟合情况较好，不能直接等价于业务效果提升。

下一步需要使用同一批 prompts 对 baseline、LoRA v1、LoRA v2 进行三方推理对比，重点看：

- 是否更稳定地礼貌拒绝违规请求
- 是否更常询问订单号或必要信息
- 是否更符合售后处理流程
- 投诉安抚是否更自然
- 是否减少泛化、偏题、重复或乱承诺

最终结论应以生成效果对比和人工/规则评价为准，不能只凭 loss 判断业务效果。
