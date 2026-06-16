"""Check v3 rule-based evaluation score files."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCORE_PATHS = {
    "baseline": PROJECT_ROOT / "outputs" / "eval_scores_baseline_v3.jsonl",
    "lora_v1": PROJECT_ROOT / "outputs" / "eval_scores_lora_v1_v3.jsonl",
    "lora_v2": PROJECT_ROOT / "outputs" / "eval_scores_lora_v2_v3.jsonl",
}
REQUIRED_FIELDS = {
    "id",
    "category",
    "difficulty",
    "model_name",
    "total_score",
    "politeness_score",
    "info_request_score",
    "policy_score",
    "next_step_score",
    "refusal_score",
    "unsafe_promise_penalty",
    "repetition_penalty",
    "length_penalty",
    "flags",
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing score file: {path}")
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc
    return rows


def average_by(rows: list[dict], field: str) -> dict[str, float]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[row[field]].append(float(row["total_score"]))
    return {key: round(mean(values), 3) for key, values in sorted(buckets.items())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check v3 evaluation scores.")
    parser.add_argument("--model_name", required=True, choices=sorted(SCORE_PATHS))
    args = parser.parse_args()

    path = SCORE_PATHS[args.model_name]
    rows = read_jsonl(path)
    if len(rows) != 100:
        raise ValueError(f"Expected 100 score rows, got {len(rows)}")

    for index, row in enumerate(rows, start=1):
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"Row {index} missing fields: {sorted(missing)}")
        if row["model_name"] != args.model_name:
            raise ValueError(f"Row {index} model_name mismatch: {row['model_name']}")
        score = float(row["total_score"])
        if not 0 <= score <= 10:
            raise ValueError(f"Row {index} total_score out of range: {score}")
        if not isinstance(row["flags"], dict):
            raise TypeError(f"Row {index} flags must be dict")

    avg_score = round(mean(float(row["total_score"]) for row in rows), 3)
    category_avg = average_by(rows, "category")
    difficulty_avg = average_by(rows, "difficulty")
    hard_rows = [row for row in rows if row["difficulty"] == "hard"]
    hard_avg = round(mean(float(row["total_score"]) for row in hard_rows), 3)
    unsafe_count = sum(bool(row["flags"].get("unsafe_promise")) for row in rows)

    print(f"Model name: {args.model_name}")
    print(f"Score file: {path}")
    print(f"Rows: {len(rows)}")
    print(f"Average score: {avg_score}")
    print(f"Category average score: {category_avg}")
    print(f"Difficulty average score: {difficulty_avg}")
    print(f"Hard average score: {hard_avg}")
    print(f"Unsafe flags count: {unsafe_count}")
    print("Eval scores v3 check completed.")


if __name__ == "__main__":
    main()
