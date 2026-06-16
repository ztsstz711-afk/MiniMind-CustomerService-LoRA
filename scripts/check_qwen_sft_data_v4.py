"""Check Qwen v4 SFT data files."""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = PROJECT_ROOT / "data" / "qwen_train_v4.jsonl"
EVAL_PATH = PROJECT_ROOT / "data" / "qwen_eval_v4.jsonl"
EXPECTED = {TRAIN_PATH: 800, EVAL_PATH: 200}


def read_and_check(path: Path, expected_count: int) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing Qwen SFT data file: {path}")
    rows = []
    pairs = Counter()
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {path} at line {line_number}")
            record = json.loads(line)
            for field in ("messages", "category", "difficulty", "tags"):
                if field not in record:
                    raise ValueError(f"{path} line {line_number} missing field: {field}")
            messages = record["messages"]
            if not isinstance(messages, list):
                raise TypeError(f"{path} line {line_number} messages must be list")
            roles = [message.get("role") for message in messages]
            if roles != ["system", "user", "assistant"]:
                raise ValueError(f"{path} line {line_number} invalid roles: {roles}")
            for message in messages:
                if not str(message.get("content", "")).strip():
                    raise ValueError(f"{path} line {line_number} has empty content for {message.get('role')}")
            if not isinstance(record["tags"], list):
                raise TypeError(f"{path} line {line_number} tags must be list")
            pairs[(messages[1]["content"], messages[2]["content"])] += 1
            rows.append(record)
    if len(rows) != expected_count:
        raise ValueError(f"{path} expected {expected_count} rows, got {len(rows)}")
    duplicate_pairs = sum(count - 1 for count in pairs.values() if count > 1)
    print(f"{path}: {len(rows)} rows")
    print(f"{path}: duplicate user+assistant pairs: {duplicate_pairs}")
    return rows


def main() -> None:
    all_rows = []
    for path, expected_count in EXPECTED.items():
        all_rows.extend(read_and_check(path, expected_count))
    category_counts = Counter(row["category"] for row in all_rows)
    difficulty_counts = Counter(row["difficulty"] for row in all_rows)
    print(f"Category counts: {dict(category_counts)}")
    print(f"Difficulty counts: {dict(difficulty_counts)}")
    print("Qwen SFT data v4 check completed.")


if __name__ == "__main__":
    main()
