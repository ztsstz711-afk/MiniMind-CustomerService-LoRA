"""Check whether the MiniMind baseline checkpoint inputs are ready."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = PROJECT_ROOT / "minimind" / "out" / "full_sft_768.pth"
TOKENIZER_FILES = (
    PROJECT_ROOT / "minimind" / "model" / "tokenizer.json",
    PROJECT_ROOT / "minimind" / "model" / "tokenizer_config.json",
)
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"


def main() -> None:
    checkpoint_exists = CHECKPOINT_PATH.is_file()
    if checkpoint_exists:
        size_mb = CHECKPOINT_PATH.stat().st_size / (1024 * 1024)
        print(f"Checkpoint found: {CHECKPOINT_PATH}")
        print(f"Checkpoint size: {size_mb:.2f} MB")
    else:
        print(f"Checkpoint missing: {CHECKPOINT_PATH}")

    tokenizer_ready = True
    for path in TOKENIZER_FILES:
        exists = path.is_file()
        tokenizer_ready = tokenizer_ready and exists
        print(f"Tokenizer file {'found' if exists else 'missing'}: {path}")

    prompts_exist = PROMPTS_PATH.is_file()
    print(
        f"Baseline prompts {'found' if prompts_exist else 'missing'}: {PROMPTS_PATH}"
    )

    ready = checkpoint_exists and tokenizer_ready and prompts_exist
    print(f"Checkpoint ready: {ready}")


if __name__ == "__main__":
    main()
