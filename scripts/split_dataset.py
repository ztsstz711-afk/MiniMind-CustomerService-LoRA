"""Shuffle and split the customer-service SFT dataset into train/eval sets."""

import json
import random
from pathlib import Path


SEED = 42
TRAIN_RATIO = 0.8
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "customer_service_sft.jsonl"
TRAIN_PATH = PROJECT_ROOT / "data" / "train.jsonl"
EVAL_PATH = PROJECT_ROOT / "data" / "eval.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Run scripts/build_dataset.py first."
        )

    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    records = read_jsonl(INPUT_PATH)
    random.seed(SEED)
    random.shuffle(records)

    split_index = int(len(records) * TRAIN_RATIO)
    train_records = records[:split_index]
    eval_records = records[split_index:]

    write_jsonl(TRAIN_PATH, train_records)
    write_jsonl(EVAL_PATH, eval_records)

    print(f"Train samples: {len(train_records)}")
    print(f"Eval samples: {len(eval_records)}")


if __name__ == "__main__":
    main()
