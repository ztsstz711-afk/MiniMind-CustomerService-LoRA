# GitHub Submission Checklist

## 应提交文件

- `README.md`
- `.gitignore`
- `PROJECT_OVERVIEW.md`
- `results_summary.md`
- `GITHUB_SUBMISSION_CHECKLIST.md`
- `scripts/`
- `data/*.jsonl` 中的小规模构造数据和评估 prompts
- `experiments/*.md`
- `notes/*.md`
- `assets/model_score_comparison.png`

## 不应提交文件或目录

- `outputs/`
- `models/`
- `minimind/`
- `data/raw_real_v5/`
- `checkpoints/`
- `__pycache__/`
- `.venv/`
- `.env`
- `*.pt`
- `*.pth`
- `*.bin`
- `*.safetensors`

## 大文件/权重检查

提交前运行：

```powershell
git status --short --ignored
```

确认以下内容只出现在 ignored 区域，不出现在 staged/untracked 待提交区域：

- Qwen 本地模型：`models/`
- MiniMind 上游仓库和 checkpoint：`minimind/`
- 推理输出和 adapter：`outputs/`
- 原始真实数据：`data/raw_real_v5/`
- 任意 `.pth`、`.pt`、`.bin`、`.safetensors`

## 如何运行图表脚本

```powershell
python scripts/plot_project_results.py
```

如果当前 Python 没有 `matplotlib`，脚本会使用标准库 fallback 生成简单 PNG，不需要安装新依赖。

输出：

```text
assets/model_score_comparison.png
```

## 如何查看项目结果

推荐阅读顺序：

1. `README.md`
2. `PROJECT_OVERVIEW.md`
3. `results_summary.md`
4. `experiments/final_evaluation_v3_summary.md`
5. `experiments/final_qwen_v4_summary.md`
6. `notes/interview_notes.md`

## 提交前检查项

- README 顶部结果表是否和实验报告一致。
- `assets/model_score_comparison.png` 是否存在。
- `PROJECT_OVERVIEW.md` 和 `results_summary.md` 是否更新。
- `notes/interview_notes.md` 是否包含 Qwen v4 和 v5 局限。
- 没有运行新训练。
- 没有下载新模型或真实大数据。
- 没有把 `outputs/`、`models/`、`minimind/` 加入 Git。

## 推荐 commit message

```text
docs: improve project overview and interview notes
```
