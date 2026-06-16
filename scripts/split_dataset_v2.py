"""Split v2 customer-service SFT data into train/eval JSONL files."""

import json
import random
from pathlib import Path


SEED = 42
TRAIN_RATIO = 0.8
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "customer_service_sft_v2.jsonl"
TRAIN_PATH = PROJECT_ROOT / "data" / "train_v2.jsonl"
EVAL_PATH = PROJECT_ROOT / "data" / "eval_v2.jsonl"


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    records = read_jsonl(INPUT_PATH)
    random.seed(SEED)
    random.shuffle(records)
    split_index = int(len(records) * TRAIN_RATIO)
    train_records = records[:split_index]
    eval_records = records[split_index:]
    write_jsonl(TRAIN_PATH, train_records)
    write_jsonl(EVAL_PATH, eval_records)
    print(f"Train v2 samples: {len(train_records)}")
    print(f"Eval v2 samples: {len(eval_records)}")
    print(f"Train path: {TRAIN_PATH}")
    print(f"Eval path: {EVAL_PATH}")


if __name__ == "__main__":
    main()
