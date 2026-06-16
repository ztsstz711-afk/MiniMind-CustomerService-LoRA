"""Wrapper for full Qwen LoRA v4 training."""

import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = Path(r"C:\Users\20112\anaconda3\envs\minimind-lora\python.exe")
TRAIN_SCRIPT = PROJECT_ROOT / "scripts" / "train_qwen_lora_v4.py"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "qwen2_5_1_5b_lora_v4"
STDOUT_PATH = PROJECT_ROOT / "outputs" / "qwen_lora_v4_train_stdout.txt"
STDERR_PATH = PROJECT_ROOT / "outputs" / "qwen_lora_v4_train_stderr.txt"
CONFIG_PATH = PROJECT_ROOT / "experiments" / "qwen_lora_v4_train_config.json"

CONFIG = {
    "model_name_or_path": str(PROJECT_ROOT / "models" / "qwen2_5_1_5b_instruct"),
    "train_file": str(PROJECT_ROOT / "data" / "qwen_train_v4.jsonl"),
    "eval_file": str(PROJECT_ROOT / "data" / "qwen_eval_v4.jsonl"),
    "output_dir": str(OUTPUT_DIR),
    "num_train_epochs": 2,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 8,
    "learning_rate": 2e-4,
    "max_seq_length": 512,
    "logging_steps": 5,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "max_grad_norm": 1.0,
    "dtype": "bfloat16",
    "use_bitsandbytes": False,
    "save_full_model": False,
}


def build_command() -> list[str]:
    return [
        str(PYTHON_EXE),
        str(TRAIN_SCRIPT),
        "--model_name_or_path",
        CONFIG["model_name_or_path"],
        "--train_file",
        CONFIG["train_file"],
        "--eval_file",
        CONFIG["eval_file"],
        "--output_dir",
        CONFIG["output_dir"],
        "--num_train_epochs",
        str(CONFIG["num_train_epochs"]),
        "--per_device_train_batch_size",
        str(CONFIG["per_device_train_batch_size"]),
        "--gradient_accumulation_steps",
        str(CONFIG["gradient_accumulation_steps"]),
        "--learning_rate",
        str(CONFIG["learning_rate"]),
        "--max_seq_length",
        str(CONFIG["max_seq_length"]),
        "--logging_steps",
        str(CONFIG["logging_steps"]),
        "--warmup_ratio",
        str(CONFIG["warmup_ratio"]),
        "--weight_decay",
        str(CONFIG["weight_decay"]),
        "--max_grad_norm",
        str(CONFIG["max_grad_norm"]),
    ]


def main() -> None:
    command = build_command()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STDOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(CONFIG)
    payload["command"] = command
    CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Qwen LoRA v4 full training wrapper starting.")
    print(f"Train script: {TRAIN_SCRIPT}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Stdout log: {STDOUT_PATH}")
    print(f"Stderr log: {STDERR_PATH}")
    print("Training config:")
    print(json.dumps(CONFIG, ensure_ascii=False, indent=2))

    env = os.environ.copy()
    env["WANDB_DISABLED"] = "true"
    env["TOKENIZERS_PARALLELISM"] = "false"

    with STDOUT_PATH.open("w", encoding="utf-8") as stdout_file, STDERR_PATH.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            stdout=stdout_file,
            stderr=stderr_file,
            env=env,
            check=False,
        )

    if completed.returncode != 0:
        raise RuntimeError(
            f"Qwen LoRA v4 training failed with exit code {completed.returncode}. "
            f"See {STDOUT_PATH} and {STDERR_PATH}."
        )
    print("Qwen LoRA v4 full training completed.")


if __name__ == "__main__":
    main()
