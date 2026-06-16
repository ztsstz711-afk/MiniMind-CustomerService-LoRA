"""Check v3 evaluation prompt dataset quality."""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"
REQUIRED_FIELDS = {
    "id",
    "category",
    "prompt",
    "expected_behavior",
    "required_elements",
    "forbidden_elements",
    "difficulty",
    "tags",
}
EXPECTED_CATEGORIES = [
    "物流查询",
    "退款进度",
    "退换货申请",
    "发票开具",
    "优惠券使用",
    "商品咨询",
    "订单取消",
    "投诉安抚",
    "拒绝不合理请求",
    "地址修改",
]


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing eval prompts file: {path}")
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {path} at line {line_number}")
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc
    return records


def main() -> None:
    records = read_jsonl(INPUT_PATH)
    if len(records) != 100:
        raise ValueError(f"Expected 100 records, got {len(records)}")

    category_counts = Counter()
    difficulty_counts = Counter()
    tag_counts = Counter()
    prompts = Counter()
    hard_count = 0

    for index, record in enumerate(records, start=1):
        missing = REQUIRED_FIELDS - set(record)
        if missing:
            raise ValueError(f"Record {index} missing fields: {sorted(missing)}")
        if not str(record["prompt"]).strip():
            raise ValueError(f"Record {index} has empty prompt")
        if not isinstance(record["required_elements"], list):
            raise TypeError(f"Record {index} required_elements must be list")
        if not isinstance(record["forbidden_elements"], list):
            raise TypeError(f"Record {index} forbidden_elements must be list")
        if not isinstance(record["tags"], list):
            raise TypeError(f"Record {index} tags must be list")
        if record["difficulty"] not in {"easy", "medium", "hard"}:
            raise ValueError(f"Record {index} invalid difficulty: {record['difficulty']}")

        category_counts[record["category"]] += 1
        difficulty_counts[record["difficulty"]] += 1
        tag_counts.update(record["tags"])
        prompts[record["prompt"]] += 1
        hard_count += int(record["difficulty"] == "hard")

        if record["category"] == "拒绝不合理请求" and record["difficulty"] != "hard":
            raise ValueError(f"Refusal record {index} must be hard")

    for category in EXPECTED_CATEGORIES:
        if category_counts[category] != 10:
            raise ValueError(
                f"Expected 10 records for {category}, got {category_counts[category]}"
            )
    complaint_hard = sum(
        1
        for record in records
        if record["category"] == "投诉安抚" and record["difficulty"] == "hard"
    )
    if complaint_hard < 7:
        raise ValueError(f"Expected at least 7 hard complaint records, got {complaint_hard}")

    duplicate_prompts = {prompt: count for prompt, count in prompts.items() if count > 1}
    if duplicate_prompts:
        raise ValueError(f"Duplicate prompts found: {duplicate_prompts}")

    print(f"Total eval prompts: {len(records)}")
    print(f"Category counts: {dict(category_counts)}")
    print(f"Difficulty distribution: {dict(difficulty_counts)}")
    print(f"Top tags: {tag_counts.most_common(20)}")
    print(f"Duplicate prompt count: {len(duplicate_prompts)}")
    print(f"Hard case count: {hard_count}")
    print("Eval prompts v3 check completed.")


if __name__ == "__main__":
    main()
