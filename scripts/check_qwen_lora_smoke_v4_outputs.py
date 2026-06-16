"""Check Qwen LoRA smoke training outputs."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "qwen_lora_smoke_v4"
STDOUT_LOG = OUTPUT_DIR / "train_stdout.txt"
STDERR_LOG = OUTPUT_DIR / "train_stderr.txt"

ERROR_PATTERN = re.compile(
    r"Traceback|CUDA out of memory|out of memory|NaN|nan|\binf\b|OSError|os error 1455|Error",
    re.IGNORECASE,
)
LOSS_PATTERN = re.compile(r"loss step=(\d+) .*? loss=([0-9.]+)")


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    if not OUTPUT_DIR.is_dir():
        raise FileNotFoundError(f"Missing output directory: {OUTPUT_DIR}")
    adapter_config = OUTPUT_DIR / "adapter_config.json"
    adapter_safe = OUTPUT_DIR / "adapter_model.safetensors"
    adapter_bin = OUTPUT_DIR / "adapter_model.bin"
    if not adapter_config.is_file():
        raise FileNotFoundError(f"Missing adapter_config.json: {adapter_config}")
    if not adapter_safe.is_file() and not adapter_bin.is_file():
        raise FileNotFoundError("Missing adapter_model.safetensors or adapter_model.bin")

    stdout = read_text(STDOUT_LOG)
    stderr = read_text(STDERR_LOG)
    losses = [(int(step), float(loss)) for step, loss in LOSS_PATTERN.findall(stdout)]
    if not losses:
        raise ValueError("No loss logs found in stdout.")
    suspicious = sorted(set(ERROR_PATTERN.findall(stdout + "\n" + stderr)))
    if suspicious:
        raise RuntimeError(f"Suspicious error patterns found: {suspicious}")

    adapter_path = adapter_safe if adapter_safe.is_file() else adapter_bin
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Adapter config: {adapter_config}")
    print(f"Adapter weights: {adapter_path}")
    print(f"Adapter size bytes: {adapter_path.stat().st_size}")
    print(f"Loss logs: {len(losses)}")
    print(f"First loss: {losses[0][1]:.6f} at step {losses[0][0]}")
    print(f"Last loss: {losses[-1][1]:.6f} at step {losses[-1][0]}")
    print(f"Stdout log: {STDOUT_LOG}")
    print(f"Stderr log: {STDERR_LOG}")
    print("Qwen LoRA smoke v4 output check completed.")


if __name__ == "__main__":
    main()
