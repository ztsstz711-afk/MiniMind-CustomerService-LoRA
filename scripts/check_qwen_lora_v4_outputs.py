"""Check full Qwen LoRA v4 training outputs."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "qwen2_5_1_5b_lora_v4"
STDOUT_PATH = PROJECT_ROOT / "outputs" / "qwen_lora_v4_train_stdout.txt"
STDERR_PATH = PROJECT_ROOT / "outputs" / "qwen_lora_v4_train_stderr.txt"
LOSS_PATTERN = re.compile(r"loss step=(\d+) .*? loss=([0-9.]+)")
ERROR_PATTERN = re.compile(
    r"CUDA out of memory|out of memory|NaN|nan|\binf\b|os error 1455|Traceback|Error",
    re.IGNORECASE,
)


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

    stdout = read_text(STDOUT_PATH)
    stderr = read_text(STDERR_PATH)
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
    print(f"Stdout log: {STDOUT_PATH} ({STDOUT_PATH.stat().st_size} bytes)")
    print(f"Stderr log: {STDERR_PATH} ({STDERR_PATH.stat().st_size} bytes)")
    print(f"Loss log count: {len(losses)}")
    print(f"First loss: {losses[0][1]:.6f} at step {losses[0][0]}")
    print(f"Last loss: {losses[-1][1]:.6f} at step {losses[-1][0]}")
    print("Qwen LoRA v4 output check completed.")


if __name__ == "__main__":
    main()
