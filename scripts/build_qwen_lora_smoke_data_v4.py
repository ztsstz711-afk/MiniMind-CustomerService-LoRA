"""Build a tiny Qwen LoRA smoke-test dataset from v4 train data."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "qwen_train_v4.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "qwen_train_smoke_v4.jsonl"
SMOKE_COUNT = 20
REQUIRED_FIELDS = {"messages", "category", "difficulty", "tags"}


def main() -> None:
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    rows = []
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if len(rows) >= SMOKE_COUNT:
                break
            if not line.strip():
                raise ValueError(f"Blank line in {INPUT_PATH} at line {line_number}")
            record = json.loads(line)
            missing = REQUIRED_FIELDS - set(record)
            if missing:
                raise ValueError(f"Line {line_number} missing fields: {sorted(missing)}")
            rows.append({
                "messages": record["messages"],
                "category": record["category"],
                "difficulty": record["difficulty"],
                "tags": record["tags"],
            })

    if len(rows) != SMOKE_COUNT:
        raise ValueError(f"Expected {SMOKE_COUNT} rows, got {len(rows)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Qwen LoRA smoke samples: {len(rows)}")
    print(f"Output path: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
