# GitHub Submission Checklist

## Goal

This checklist helps keep the repository safe and readable before GitHub submission.

The project contains local model files and generated outputs.

Those files should not be committed.

## Files To Submit

- `README.md`
- `.gitignore`
- `PROJECT_OVERVIEW.md`
- `results_summary.md`
- `GITHUB_SUBMISSION_CHECKLIST.md`
- `notes/interview_notes.md`
- `scripts/`
- `data/*.jsonl` for small constructed datasets
- `experiments/*.md`
- `assets/model_score_comparison.png`

## Files Not To Submit

- `outputs/`
- `models/`
- `minimind/`
- `data/raw_real_v5/`
- `checkpoints/`
- `__pycache__/`
- `.venv/`
- `.env`

## Weight Files Not To Submit

- `*.pt`
- `*.pth`
- `*.bin`
- `*.safetensors`

## Why These Files Are Ignored

`outputs/` contains generated inference results and LoRA adapters.

`models/` contains local Qwen model weights.

`minimind/` contains the cloned upstream MiniMind repository and checkpoints.

`data/raw_real_v5/` is reserved for local raw real-world data.

These files are either too large, generated locally, or unsuitable for GitHub submission.

## Check Git Status

Run:

```powershell
git status --short --ignored
```

Safe ignored entries include:

- `!! outputs/`
- `!! models/`
- `!! minimind/`
- `!! data/raw_real_v5/`
- `!! scripts/__pycache__/`

Dangerous entries include:

- any `.pth` file not ignored
- any `.safetensors` file not ignored
- any model file under normal untracked status
- any raw real data file under normal untracked status

## Check Markdown Files

Run:

```powershell
python -c "from pathlib import Path; files=['README.md','PROJECT_OVERVIEW.md','results_summary.md','notes/interview_notes.md','GITHUB_SUBMISSION_CHECKLIST.md']; [print(f, len(Path(f).read_text(encoding='utf-8').splitlines())) for f in files]"
```

Each Markdown file should have real line breaks.

README should not appear as one long raw line on GitHub.

## Generate Chart

Run:

```powershell
python scripts/plot_project_results.py
```

Expected output:

```text
assets/model_score_comparison.png
```

If matplotlib is unavailable, the script uses a standard-library fallback.

## Recommended Reading Order

1. `README.md`
2. `PROJECT_OVERVIEW.md`
3. `results_summary.md`
4. `notes/interview_notes.md`
5. `experiments/final_qwen_v4_summary.md`

## Before Commit

Confirm no training was run.

Confirm no model was downloaded.

Confirm no raw real data was added.

Confirm no output adapter was staged.

Confirm no upstream MiniMind files were staged.

Confirm the score table still contains:

- MiniMind baseline: 5.025
- MiniMind LoRA v1: 5.375
- MiniMind LoRA v2: 5.645
- Qwen baseline: 6.275
- Qwen LoRA v4: 7.865

## Recommended Commit Message

```text
docs: rebuild markdown docs with real line breaks
```
