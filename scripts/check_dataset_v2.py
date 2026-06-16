"""Validate the v2 customer-service SFT dataset."""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "customer_service_sft_v2.jsonl"
REQUIRED_FIELDS = {"instruction", "input", "output", "category", "difficulty", "tags"}
REFUSAL_WORDS = ("无法", "不能", "不支持", "不符合规则")
APPEASE_WORDS = ("抱歉", "理解", "很抱歉")


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Missing dataset: {DATA_PATH}")

    records = []
    category_counts = Counter()
    difficulty_counts = Counter()
    tag_counts = Counter()
    pairs = Counter()
    output_lengths = []
    missing_fields = []
    empty_fields = []

    with DATA_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line at {line_number}")
            record = json.loads(line)
            missing = REQUIRED_FIELDS - set(record)
            if missing:
                missing_fields.append((line_number, sorted(missing)))
                continue
            if not str(record["input"]).strip() or not str(record["output"]).strip():
                empty_fields.append(line_number)
            if record["difficulty"] not in {"easy", "medium", "hard"}:
                raise ValueError(f"Invalid difficulty at line {line_number}: {record['difficulty']}")
            if not isinstance(record["tags"], list) or not record["tags"]:
                raise ValueError(f"Invalid tags at line {line_number}")

            records.append(record)
            category_counts[record["category"]] += 1
            difficulty_counts[record["difficulty"]] += 1
            tag_counts.update(record["tags"])
            pairs[(record["input"], record["output"])] += 1
            output_lengths.append(len(record["output"]))

    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields[:5]}")
    if empty_fields:
        raise ValueError(f"Empty input/output lines: {empty_fields[:10]}")

    duplicates = [pair for pair, count in pairs.items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate input+output pairs found: {len(duplicates)}")

    refusal_records = [r for r in records if r["category"] == "拒绝不合理请求"]
    weak_refusals = [
        r["input"] for r in refusal_records
        if not any(word in r["output"] for word in REFUSAL_WORDS)
    ]
    if weak_refusals:
        raise ValueError(f"Refusal records missing refusal expression: {weak_refusals[:5]}")

    complaint_records = [r for r in records if r["category"] == "投诉安抚"]
    weak_complaints = [
        r["input"] for r in complaint_records
        if not any(word in r["output"] for word in APPEASE_WORDS)
    ]
    if weak_complaints:
        raise ValueError(f"Complaint records missing appeasement expression: {weak_complaints[:5]}")

    print(f"Total samples: {len(records)}")
    print(f"Category counts: {dict(sorted(category_counts.items()))}")
    print(f"Difficulty distribution: {dict(sorted(difficulty_counts.items()))}")
    print(f"Top tags: {tag_counts.most_common(20)}")
    print(
        "Output length min/avg/max: "
        f"{min(output_lengths)}/{sum(output_lengths) / len(output_lengths):.1f}/{max(output_lengths)}"
    )
    print(f"Duplicate input+output pairs: {len(duplicates)}")
    print(f"Refusal records checked: {len(refusal_records)}")
    print(f"Complaint records checked: {len(complaint_records)}")
    print("Dataset v2 check completed.")


if __name__ == "__main__":
    main()
