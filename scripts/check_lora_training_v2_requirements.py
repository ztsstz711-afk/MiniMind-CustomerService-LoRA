"""Check MiniMind LoRA v2 training prerequisites without starting training."""

import json
from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_LORA_PATH = PROJECT_ROOT / "minimind" / "trainer" / "train_lora.py"
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "minimind_train_v2.jsonl"
EVAL_DATA_PATH = PROJECT_ROOT / "data" / "minimind_eval_v2.jsonl"
CHECKPOINT_PATH = PROJECT_ROOT / "minimind" / "out" / "full_sft_768.pth"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "lora_customer_service_v2"
TOKENIZER_FILES = (
    PROJECT_ROOT / "minimind" / "model" / "tokenizer.json",
    PROJECT_ROOT / "minimind" / "model" / "tokenizer_config.json",
)

EXPECTED_TRAIN_SAMPLES = 800
EXPECTED_EVAL_SAMPLES = 200


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
    if train_count != EXPECTED_TRAIN_SAMPLES:
        raise ValueError(f"Expected 800 train samples, got {train_count}")
    if eval_count != EXPECTED_EVAL_SAMPLES:
        raise ValueError(f"Expected 200 eval samples, got {eval_count}")
    print(f"Train v2 samples: {train_count}")
    print(f"Eval v2 samples: {eval_count}")

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
        raise RuntimeError("CUDA is not available; LoRA v2 training should not start.")

    print(f"Output directory to use: {OUTPUT_DIR}")
    print("Suggested LoRA v2 config:")
    print("  batch_size: 4")
    print("  accumulation_steps: 4")
    print("  effective_batch_size: 16")
    print("  max_seq_len: 340")
    print("  epochs: 3")
    print("  learning_rate: 1e-4")
    print("  dtype: bfloat16")
    print("LoRA v2 training requirements check completed.")


if __name__ == "__main__":
    main()
