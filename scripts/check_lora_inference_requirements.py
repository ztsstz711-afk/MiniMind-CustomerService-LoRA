"""Check LoRA inference inputs without running generation."""

from pathlib import Path

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_CHECKPOINT_PATH = PROJECT_ROOT / "minimind" / "out" / "full_sft_768.pth"
LORA_CHECKPOINT_PATH = (
    PROJECT_ROOT / "outputs" / "lora_customer_service" / "lora_customer_service_768.pth"
)
TOKENIZER_FILES = (
    PROJECT_ROOT / "minimind" / "model" / "tokenizer.json",
    PROJECT_ROOT / "minimind" / "model" / "tokenizer_config.json",
)
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"Found: {path} ({size_mb:.2f} MB)")


def main() -> None:
    require_file(BASE_CHECKPOINT_PATH)
    require_file(LORA_CHECKPOINT_PATH)
    for tokenizer_file in TOKENIZER_FILES:
        require_file(tokenizer_file)
    require_file(PROMPTS_PATH)

    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    print(
        "GPU name: "
        + (torch.cuda.get_device_name(0) if cuda_available else "no cuda")
    )
    print("LoRA inference requirements check completed.")


if __name__ == "__main__":
    main()
