"""Wrapper for launching MiniMind LoRA training with project-local settings.

This script does not modify MiniMind source code. It starts training only when
the user explicitly runs this wrapper.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = Path(r"C:\Users\20112\anaconda3\envs\minimind-lora\python.exe")
MINIMIND_ROOT = PROJECT_ROOT / "minimind"
TRAINER_DIR = MINIMIND_ROOT / "trainer"
TRAIN_SCRIPT = TRAINER_DIR / "train_lora.py"
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "minimind_train.jsonl"
BASE_CHECKPOINT_PATH = MINIMIND_ROOT / "out" / "full_sft_768.pth"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "lora_customer_service"
STDOUT_PATH = PROJECT_ROOT / "outputs" / "lora_train_stdout.txt"
STDERR_PATH = PROJECT_ROOT / "outputs" / "lora_train_stderr.txt"
CONFIG_PATH = PROJECT_ROOT / "experiments" / "lora_train_config.json"

CONFIG = {
    "python_executable": str(PYTHON_EXE),
    "working_directory": str(TRAINER_DIR),
    "train_script": str(TRAIN_SCRIPT),
    "data_path": str(TRAIN_DATA_PATH),
    "base_checkpoint": str(BASE_CHECKPOINT_PATH),
    "save_dir": str(OUTPUT_DIR),
    "lora_name": "lora_customer_service",
    "from_weight": "full_sft",
    "batch_size": 4,
    "accumulation_steps": 4,
    "effective_batch_size": 16,
    "epochs": 3,
    "learning_rate": 1e-4,
    "max_seq_len": 340,
    "device": "cuda:0",
    "dtype": "bfloat16",
    "num_workers": 0,
    "log_interval": 5,
    "save_interval": 100,
    "from_resume": 0,
    "use_wandb": False,
    "stdout_path": str(STDOUT_PATH),
    "stderr_path": str(STDERR_PATH),
    "expected_lora_checkpoint": str(OUTPUT_DIR / "lora_customer_service_768.pth"),
}


def build_command() -> list[str]:
    return [
        str(PYTHON_EXE),
        "train_lora.py",
        "--save_dir",
        str(OUTPUT_DIR),
        "--lora_name",
        CONFIG["lora_name"],
        "--epochs",
        str(CONFIG["epochs"]),
        "--batch_size",
        str(CONFIG["batch_size"]),
        "--learning_rate",
        str(CONFIG["learning_rate"]),
        "--device",
        CONFIG["device"],
        "--dtype",
        CONFIG["dtype"],
        "--num_workers",
        str(CONFIG["num_workers"]),
        "--accumulation_steps",
        str(CONFIG["accumulation_steps"]),
        "--log_interval",
        str(CONFIG["log_interval"]),
        "--save_interval",
        str(CONFIG["save_interval"]),
        "--hidden_size",
        "768",
        "--num_hidden_layers",
        "8",
        "--max_seq_len",
        str(CONFIG["max_seq_len"]),
        "--use_moe",
        "0",
        "--data_path",
        str(TRAIN_DATA_PATH),
        "--from_weight",
        CONFIG["from_weight"],
        "--from_resume",
        str(CONFIG["from_resume"]),
        "--use_compile",
        "0",
    ]


def validate_prerequisites() -> None:
    required_files = [
        PYTHON_EXE,
        TRAIN_SCRIPT,
        TRAIN_DATA_PATH,
        BASE_CHECKPOINT_PATH,
        MINIMIND_ROOT / "model" / "tokenizer.json",
        MINIMIND_ROOT / "model" / "tokenizer_config.json",
    ]
    missing = [path for path in required_files if not path.exists()]
    if missing:
        rendered = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required file(s):\n{rendered}")


def write_config(command: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STDOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(CONFIG)
    payload["command"] = command
    payload["command_string"] = " ".join(f'"{part}"' if " " in part else part for part in command)
    CONFIG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    validate_prerequisites()
    command = build_command()
    write_config(command)

    print("LoRA training wrapper is starting MiniMind train_lora.py.")
    print(f"Working directory: {TRAINER_DIR}")
    print(f"Data path: {TRAIN_DATA_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("wandb/swanlab: disabled (no --use_wandb flag)")
    print(f"Stdout log: {STDOUT_PATH}")
    print(f"Stderr log: {STDERR_PATH}")

    env = os.environ.copy()
    env["WANDB_MODE"] = "offline"
    env["SWANLAB_MODE"] = "offline"

    with STDOUT_PATH.open("w", encoding="utf-8") as stdout_file, STDERR_PATH.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        completed = subprocess.run(
            command,
            cwd=TRAINER_DIR,
            stdout=stdout_file,
            stderr=stderr_file,
            env=env,
            check=False,
        )

    if completed.returncode != 0:
        raise RuntimeError(
            f"LoRA training failed with exit code {completed.returncode}. "
            f"See {STDERR_PATH} and {STDOUT_PATH}."
        )
    print("LoRA training completed.")


if __name__ == "__main__":
    main()
