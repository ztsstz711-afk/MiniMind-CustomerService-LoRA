# Real Data Source Survey v5

## 调研目标

v5 希望引入公开中文电商客服真实语料，增强 Qwen LoRA 的真实用户表达、多轮客服沟通和回复自然度。当前阶段只做数据源调研、README/文件列表阅读和格式记录，不下载完整大数据集，不训练。

## 当前结论

最匹配方向仍是 JDDC / JDDC 2.0 系列，因为它直接面向中文电商客服多轮对话。问题是数据规模很大，且公开入口更像挑战集/论文数据入口，不适合在本阶段直接下载全量。

更务实的落地候选是 CSDS：它基于 JDDC 选取真实客服对话，并有官方 GitHub 与网盘/Google Drive 下载入口。虽然主任务是客服对话摘要，不是直接回复生成，但可作为小规模真实客服对话结构探测数据源，用于抽取用户/客服轮次或分析真实表达。

2026-06-17 进一步探测 `https://github.com/hrlinlp/jddc2.1` 后确认：JDDC 2.1 GitHub 仓库公开文件列表只有 `README.md`，没有可直接下载的 `data/`、`sample/`、`dev/`、`test/` 文件，也没有 GitHub Release。README 说明如需数据集，需要填写申请表并使用机构邮箱发送给作者。仓库 README 未提供按 text/dialogue/image/knowledge 分块下载的公开链接，因此本阶段不能直接只下载文本 dialogue 子集。

## 候选数据源

| 数据源 | 任务类型 | 是否适合客服回复生成 | 数据规模 | 是否可能太大 | 许可/使用风险 | sample/dev/test 小文件 | 推荐程度 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JDDC | 中文电商客服多轮对话，含 task-oriented / QA / chitchat 等 | 很适合，领域最匹配，可抽取 user -> agent pairs | 论文描述超过 100 万多轮对话、2000 万 utterances、1.5 亿词 | 是，完整数据很大 | 需确认挑战赛/数据集许可、引用要求、脱敏要求 | 论文提到 challenge sets，但本轮未找到可靠小样本直接下载入口 | 高 |
| JDDC 2.0 / JDDC 2.1 | 中文电商客服多模态多轮对话 | 文本部分适合，但多模态信息对当前 Qwen 文本 LoRA 暂时不是刚需 | JDDC 2.0 论文描述约 24.6 万 sessions、300 万 utterances、50.7 万 images | 是，图像导致体积更大 | 多模态数据许可和下载体积风险更高 | 本轮未找到 <50MB 的可确认 sample 文件 | 中高，优先只取文本子集 |
| CSDS | 中文客服对话摘要 | 中等适合。原始对话可用于学习真实表达，但标注目标是摘要，不是下一轮回复 | 论文表格：train/dev/test 为 9101 / 800 / 800 dialogues | 中等，明显小于 JDDC；仍需确认压缩包大小 | 官方 GitHub 提供下载入口；需遵守论文引用和数据使用说明 | 官方 GitHub 提供 Baidu NetDisk / Google Drive 下载入口，但本轮未下载 | 中高，建议下一步优先探测 |
| Topic-Oriented Spoken Dialogue Summarization customer-service dataset | 中文客服对话摘要 | 不适合作为主训练数据；可作为真实客服摘要/结构参考 | CSDS 论文对比表提到 17189 / 820 / 851 dialogues | 中等 | 论文指出公开数据难分析，句子用 word indexes 表示，可读性差 | 未找到便利小样本入口 | 低 |
| CrossWOZ | 中文跨领域任务型对话 | 不太适合电商客服回复生成，但可参考任务型对话格式 | 约 6000 sessions、102000 utterances，酒店/餐馆/景点/地铁/出租 | 不算太大 | 非电商客服领域，迁移风险 | 有公开数据集，但领域不匹配 | 低 |
| NaturalConv | 中文多轮开放域/话题驱动对话 | 不适合作为客服回复主数据；可用于自然口语表达参考 | 约 1.99 万 conversations、40 万 utterances | 中等 | 非客服、非电商，容易稀释合规售后风格 | 腾讯 AI Lab 数据入口可查 | 低 |

## 数据源细节

### JDDC

- 名称：The JDDC Corpus: A Large-Scale Multi-Turn Chinese Dialogue Dataset for E-commerce Customer Service
- 论文入口：https://arxiv.org/abs/1911.09969
- 任务类型：真实中文电商客服多轮对话。
- 规模：论文摘要描述超过 100 万多轮对话、2000 万 utterances、1.5 亿词。
- 适配价值：最高。它直接覆盖电商客服、售前售后、多轮上下文，最适合 v5 的真实数据增强目标。
- 风险：体积大；本轮未发现稳定小样本下载入口；需要确认数据许可、脱敏情况和引用要求。
- v5 建议：不要直接下载全量。优先寻找 dev/challenge/sample 小文件，或手动下载一个小切片后用 `scripts/inspect_real_data_v5.py` 检查格式。

### JDDC 2.0 / JDDC 2.1

- 名称：The JDDC 2.0 Corpus: A Large-Scale Multimodal Multi-Turn Chinese Dialogue Dataset for E-commerce Customer Service
- JDDC 2.1 GitHub：https://github.com/hrlinlp/jddc2.1
- 论文入口：https://arxiv.org/abs/2109.12913
- 任务类型：多模态中文电商客服多轮对话。
- 规模：论文摘要描述约 24.6 万 sessions、300 万 utterances、50.7 万 images。
- 适配价值：文本轮次有价值，但图片/视频等多模态字段当前不进入 Qwen 文本 LoRA。
- 风险：多模态数据体积很大；格式更复杂；JDDC 2.1 的公开稳定入口本轮未确认。
- v5 建议：如果能获得纯文本子集或小 sample，可作为 JDDC 的替代入口；否则优先普通 JDDC/CSDS。

#### JDDC 2.1 GitHub 仓库探测记录

- 探测日期：2026-06-17
- 仓库：`hrlinlp/jddc2.1`
- 仓库文件列表：仅看到 `README.md`
- GitHub releases：无公开 release
- README 数据申请方式：填写 application form（docx 或 pdf）并用机构邮箱发送给 `lihaoran24 (AT) jd.com`
- 是否有直接 data 下载链接：未发现
- 是否区分 text/dialogue/image/knowledge 下载：README 未提供公开分块下载说明
- 是否有 sample/dev/test 小文件：未发现
- 是否可以只下载文本 dialogue 部分：公开仓库中无法确认；可能需要申请数据后再询问作者是否提供文本-only 子集
- 是否需要下载完整压缩包：公开 README 未说明压缩包结构；无法确认是否必须全量下载
- 是否适合抽样 1000~3000 条：如果申请后能获得文本 dialogue 文件或小切片，则非常适合；如果只能获取包含图片的完整大包，则不适合当前轻量 v5 探测阶段
- 如果可行，推荐下载哪个最小文件：公开仓库未提供可下载小文件；建议申请时明确请求 text/dialogue-only sample 或 dev split，避免图片和完整多模态大包

阶段性判断：JDDC 2.1 是领域最匹配的数据源之一，但当前 GitHub 仓库不是直接下载入口，而是申请入口。本阶段不建议下载全量，也无法下载 `<50MB` 小样本。若需要继续使用 JDDC 2.1，建议手动提交申请，并在邮件中明确说明只需要文本 dialogue 子集或 sample/dev split。

### CSDS

- 名称：CSDS: A Fine-Grained Chinese Dataset for Customer Service Dialogue Summarization
- 论文入口：https://arxiv.org/abs/2108.13139
- 官方 GitHub：https://github.com/xiaolinAndy/CSDS
- 任务类型：中文客服对话摘要，包含 overall summary、user summary、agent summary。
- 规模：论文表格显示 train/dev/test 为 9101 / 800 / 800 dialogues。
- 下载入口：官方 GitHub README 提供 Baidu NetDisk 和 Google Drive。
- 适配价值：中高。虽然不是客服回复生成数据，但它基于 JDDC 对话选取和标注，能用于观察真实客服对话结构，也可能抽取相邻 user/agent 轮次做 SFT。
- 风险：摘要任务的 agent summary 不是原始下一轮回复；直接训练可能让模型偏向摘要而不是客服回复。需要优先使用 raw dialogue turns，而不是 summary。
- v5 建议：作为第一批可落地探测数据源。下一步手动下载或只下载小文件后放到 `data/raw_real_v5/`，用 inspect 脚本确认 JSON 字段。

### 其他小规模中文客服/电商对话数据

本轮未发现比 CSDS 更直接、许可更清晰、且适合小规模探测的中文电商客服回复生成数据。通用中文对话数据如 CrossWOZ、NaturalConv 可以提供多轮格式或自然表达参考，但领域不是电商售后客服，直接混入训练可能稀释合规规则和售后流程。

## 小样本下载情况

- 本轮没有下载任何完整数据集。
- 本轮没有发现可确认小于 50MB、且无需跳转网盘/登录的大规模数据 sample 文件。
- JDDC 2.1 GitHub 仓库未提供 sample/dev/test 小文件，因此未下载任何 JDDC 2.1 文件。
- 已创建 `data/raw_real_v5/README.md` 作为后续本地原始数据目录说明。
- 已在 `.gitignore` 中加入 `data/raw_real_v5/`，避免原始真实数据被提交。

## 推荐路线

1. 不建议在当前阶段下载 JDDC 2.1 全量数据。它需要申请，且公开仓库未说明可分块下载文本 dialogue。
2. 如果坚持 JDDC 2.1，建议先手动申请 text/dialogue-only sample 或 dev split，不要下载图片和完整多模态大包。
3. 优先使用 CSDS 做第一轮真实数据格式探测，因为它有官方 GitHub 和明确下载入口，规模比 JDDC 更可控。
4. 下载后先不要训练，只运行：

```powershell
python scripts/inspect_real_data_v5.py --data_path data/raw_real_v5/<downloaded_file>
```

5. 根据实际字段改造 `scripts/convert_jddc_to_qwen_sft_v5.py`，优先抽取原始 dialogue 中相邻 user -> assistant pair。
6. 抽取 1000~3000 条真实客服 pair 后，与 `data/qwen_train_v4.jsonl` 混合。
7. 保留 synthetic compliance hard cases，避免真实数据削弱拒答边界。

## 参考来源

- JDDC paper: https://arxiv.org/abs/1911.09969
- JDDC 2.0 paper: https://arxiv.org/abs/2109.12913
- JDDC 2.1 GitHub: https://github.com/hrlinlp/jddc2.1
- CSDS paper: https://arxiv.org/abs/2108.13139
- CSDS official GitHub: https://github.com/xiaolinAndy/CSDS
- NaturalConv paper: https://arxiv.org/abs/2103.02548
- CrossWOZ paper: https://arxiv.org/abs/2002.11893
