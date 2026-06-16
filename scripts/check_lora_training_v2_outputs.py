"""Check MiniMind LoRA v2 training outputs and logs."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LORA_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "lora_customer_service_v2"
STDOUT_PATH = PROJECT_ROOT / "outputs" / "lora_train_v2_stdout.txt"
STDERR_PATH = PROJECT_ROOT / "outputs" / "lora_train_v2_stderr.txt"

LOSS_PATTERN = re.compile(
    r"Epoch:\[(?P<epoch>[^\]]+)\]\((?P<step>[^\)]+)\), loss: (?P<loss>[0-9.]+)"
)
ERROR_PATTERN = re.compile(
    r"Error|Traceback|CUDA out of memory|out of memory|NaN|nan|\binf\b|checkpoint mismatch|mismatch|RuntimeError",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required log file not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    if not LORA_OUTPUT_DIR.is_dir():
        raise FileNotFoundError(f"LoRA v2 output directory not found: {LORA_OUTPUT_DIR}")
    print(f"LoRA v2 output directory: {LORA_OUTPUT_DIR}")

    files = sorted(path for path in LORA_OUTPUT_DIR.iterdir() if path.is_file())
    print("LoRA v2 output files:")
    if files:
        for path in files:
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  {path.name}: {size_mb:.2f} MB ({path.stat().st_size} bytes)")
    else:
        print("  none")

    stdout_text = read_text(STDOUT_PATH)
    stderr_text = read_text(STDERR_PATH)
    print(f"stdout log: {STDOUT_PATH} ({STDOUT_PATH.stat().st_size} bytes)")
    print(f"stderr log: {STDERR_PATH} ({STDERR_PATH.stat().st_size} bytes)")

    losses = [
        (match.group("epoch"), match.group("step"), float(match.group("loss")))
        for match in LOSS_PATTERN.finditer(stdout_text)
    ]
    print(f"loss log count: {len(losses)}")
    if losses:
        first_epoch, first_step, first_loss = losses[0]
        last_epoch, last_step, last_loss = losses[-1]
        print(f"first loss: {first_loss:.4f} at epoch {first_epoch}, step {first_step}")
        print(f"last loss: {last_loss:.4f} at epoch {last_epoch}, step {last_step}")

    stdout_matches = sorted(set(match.group(0) for match in ERROR_PATTERN.finditer(stdout_text)))
    stderr_matches = sorted(set(match.group(0) for match in ERROR_PATTERN.finditer(stderr_text)))
    print(f"stdout suspicious patterns: {stdout_matches if stdout_matches else 'none'}")
    print(f"stderr suspicious patterns: {stderr_matches if stderr_matches else 'none'}")
    if stdout_matches or stderr_matches:
        raise RuntimeError("Suspicious error/numeric patterns found in v2 training logs.")

    print("LoRA v2 training output check completed.")


if __name__ == "__main__":
    main()
