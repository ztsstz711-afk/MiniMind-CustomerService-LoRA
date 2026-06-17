# Release Checklist

## Goal

This checklist keeps the repository clean before publishing or tagging a documentation release.

The project contains local model files, generated outputs, and raw-data placeholders.

Those files should stay out of version control.

## Files To Keep In Version Control

- `README.md`
- `.gitignore`
- `PROJECT_OVERVIEW.md`
- `results_summary.md`
- `RELEASE_CHECKLIST.md`
- `notes/experiment_notes.md`
- `scripts/`
- small constructed JSONL datasets under `data/`
- Markdown experiment records under `experiments/`
- `assets/model_score_comparison.png`

## Files To Keep Out Of Version Control

- `outputs/`
- `models/`
- `minimind/`
- `data/raw_real_v5/`
- `checkpoints/`
- `__pycache__/`
- `.venv/`
- `.env`

## Model Weight Patterns To Exclude

- `*.pt`
- `*.pth`
- `*.bin`
- `*.safetensors`

## Repository Hygiene Checks

Run:

```powershell
git status --short --ignored
```

Expected ignored local directories:

- `!! outputs/`
- `!! models/`
- `!! minimind/`
- `!! data/raw_real_v5/`
- `!! scripts/__pycache__/`

Unexpected items to investigate:

- model weights outside ignored directories
- generated adapters in normal untracked status
- raw customer-service data in normal untracked status
- cache files in normal untracked status

## Result Files

The main public result files are:

- `PROJECT_OVERVIEW.md`
- `results_summary.md`
- `experiments/final_evaluation_v3_summary.md`
- `experiments/final_qwen_v4_summary.md`
- `assets/model_score_comparison.png`

## Chart Generation

Run:

```powershell
python scripts/plot_project_results.py
```

Expected output:

```text
assets/model_score_comparison.png
```

If matplotlib is unavailable, the script uses a standard-library fallback.

## Markdown Line Check

Run:

```powershell
python -c "from pathlib import Path; files=['README.md','PROJECT_OVERVIEW.md','results_summary.md','notes/experiment_notes.md','RELEASE_CHECKLIST.md']; [print(f, len(Path(f).read_text(encoding='utf-8').splitlines())) for f in files]"
```

The files should have real line breaks.

## Score Consistency Check

Confirm these values remain unchanged:

- MiniMind baseline: 5.025
- MiniMind LoRA v1: 5.375
- MiniMind LoRA v2: 5.645
- Qwen baseline: 6.275
- Qwen LoRA v4: 7.865

## Before Release

Confirm no new training was run.

Confirm no model was downloaded.

Confirm no raw private data was added.

Confirm no generated adapter was staged.

Confirm no upstream MiniMind files were staged.
