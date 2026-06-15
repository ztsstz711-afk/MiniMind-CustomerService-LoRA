"""Check MiniMind LoRA training prerequisites without starting training."""

import json
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_LORA_PATH = PROJECT_ROOT / "minimind" / "trainer" / "train_lora.py"
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "minimind_train.jsonl"
EVAL_DATA_PATH = PROJECT_ROOT / "data" / "minimind_eval.jsonl"
CHECKPOINT_PATH = PROJECT_ROOT / "minimind" / "out" / "full_sft_768.pth"
TOKENIZER_FILES = (
    PROJECT_ROOT / "minimind" / "model" / "tokenizer.json",
    PROJECT_ROOT / "minimind" / "model" / "tokenizer_config.json",
)

SUGGESTED_BATCH_SIZE = 4
SUGGESTED_ACCUMULATION_STEPS = 4
SUGGESTED_MAX_SEQ_LEN = 340
SUGGESTED_EPOCHS = 3
SUGGESTED_LEARNING_RATE = "1e-4"


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    print(f"Found: {path}")


def count_jsonl(path: Path) -> int:
    require_file(path)
    count = 0
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {path} at line {line_number}")
            record = json.loads(line)
            if "conversations" not in record:
                raise ValueError(
                    f"Missing conversations in {path} at line {line_number}"
                )
            count += 1
    return count


def main() -> None:
    require_file(TRAIN_LORA_PATH)

    train_count = count_jsonl(TRAIN_DATA_PATH)
    eval_count = count_jsonl(EVAL_DATA_PATH)
    if train_count != 240:
        raise ValueError(f"Expected 240 train samples, got {train_count}")
    if eval_count != 60:
        raise ValueError(f"Expected 60 eval samples, got {eval_count}")
    print(f"Train samples: {train_count}")
    print(f"Eval samples: {eval_count}")

    require_file(CHECKPOINT_PATH)
    for tokenizer_file in TOKENIZER_FILES:
        require_file(tokenizer_file)

    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    print(
        "GPU name: "
        + (torch.cuda.get_device_name(0) if cuda_available else "no cuda")
    )
    if not cuda_available:
        raise RuntimeError("CUDA is not available; LoRA training should not start.")

    print("Suggested LoRA config:")
    print(f"  batch_size: {SUGGESTED_BATCH_SIZE}")
    print(f"  accumulation_steps: {SUGGESTED_ACCUMULATION_STEPS}")
    print(f"  effective_batch_size: {SUGGESTED_BATCH_SIZE * SUGGESTED_ACCUMULATION_STEPS}")
    print(f"  max_seq_len: {SUGGESTED_MAX_SEQ_LEN}")
    print(f"  epochs: {SUGGESTED_EPOCHS}")
    print(f"  learning_rate: {SUGGESTED_LEARNING_RATE}")
    print("LoRA training requirements check completed.")


if __name__ == "__main__":
    main()
