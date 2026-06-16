"""Compare v3 rule-based scores across baseline, LoRA v1, and LoRA v2."""

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
JSON_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "eval_score_comparison_v3.json"
MARKDOWN_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "eval_score_comparison_v3.md"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing score file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def avg(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def average_by(rows: list[dict], field: str) -> dict[str, float]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[row[field]].append(float(row["total_score"]))
    return {key: avg(values) for key, values in sorted(buckets.items())}


def sum_field(rows: list[dict], field: str) -> float:
    return round(sum(float(row[field]) for row in rows), 3)


def summarize(rows: list[dict]) -> dict:
    refusal_rows = [row for row in rows if row["category"] == "拒绝不合理请求"]
    return {
        "overall_average_score": avg([float(row["total_score"]) for row in rows]),
        "category_average_score": average_by(rows, "category"),
        "difficulty_average_score": average_by(rows, "difficulty"),
        "refusal_category_average_score": avg([float(row["total_score"]) for row in refusal_rows]),
        "refusal_present_count": sum(bool(row["flags"].get("refusal_present")) for row in refusal_rows),
        "refusal_total": len(refusal_rows),
        "unsafe_flags_count": sum(bool(row["flags"].get("unsafe_promise")) for row in rows),
        "repetition_penalty_sum": sum_field(rows, "repetition_penalty"),
        "length_penalty_sum": sum_field(rows, "length_penalty"),
        "unsafe_promise_penalty_sum": sum_field(rows, "unsafe_promise_penalty"),
    }


def delta_map(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    keys = sorted(set(left) | set(right))
    return {key: round(right.get(key, 0.0) - left.get(key, 0.0), 3) for key in keys}


def best_by_category(summaries: dict[str, dict]) -> dict[str, dict]:
    categories = sorted(summaries["baseline"]["category_average_score"])
    result = {}
    for category in categories:
        scores = {
            model: summary["category_average_score"][category]
            for model, summary in summaries.items()
        }
        best_score = max(scores.values())
        winners = [model for model, score in scores.items() if score == best_score]
        result[category] = {"best_model": winners, "scores": scores}
    return result


def validate_alignment(rows_by_model: dict[str, list[dict]]) -> None:
    lengths = {model: len(rows) for model, rows in rows_by_model.items()}
    if set(lengths.values()) != {100}:
        raise ValueError(f"Expected 100 rows for every model, got {lengths}")
    baseline = rows_by_model["baseline"]
    for model, rows in rows_by_model.items():
        for index, (base, row) in enumerate(zip(baseline, rows), start=1):
            for field in ("id", "category", "difficulty"):
                if base[field] != row[field]:
                    raise ValueError(f"{field} mismatch for {model} at row {index}")


def write_markdown(summaries: dict[str, dict], comparison: dict) -> None:
    models = ["baseline", "lora_v1", "lora_v2"]
    lines = [
        "# Eval Score Comparison v3",
        "",
        "Rule-based rubric can only provide coarse automatic evaluation. It does not fully represent real business quality, factual correctness, or compliance reliability.",
        "",
        "## Overall Average Score",
        "",
        "| model | overall_avg | unsafe_flags | refusal_avg | refusal_present | repetition_penalty | length_penalty |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model in models:
        summary = summaries[model]
        lines.append(
            f"| {model} | {summary['overall_average_score']} | {summary['unsafe_flags_count']} | "
            f"{summary['refusal_category_average_score']} | {summary['refusal_present_count']}/{summary['refusal_total']} | "
            f"{summary['repetition_penalty_sum']} | {summary['length_penalty_sum']} |"
        )

    lines.extend(["", "## Category Average Score", ""])
    categories = sorted(summaries["baseline"]["category_average_score"])
    lines.extend(["| category | baseline | lora_v1 | lora_v2 | best_model |", "| --- | ---: | ---: | ---: | --- |"])
    for category in categories:
        best = comparison["best_by_category"][category]
        lines.append(
            f"| {category} | {best['scores']['baseline']} | {best['scores']['lora_v1']} | "
            f"{best['scores']['lora_v2']} | {', '.join(best['best_model'])} |"
        )

    lines.extend(["", "## Difficulty Average Score", ""])
    difficulties = sorted(summaries["baseline"]["difficulty_average_score"])
    lines.extend(["| difficulty | baseline | lora_v1 | lora_v2 |", "| --- | ---: | ---: | ---: |"])
    for difficulty in difficulties:
        lines.append(
            f"| {difficulty} | {summaries['baseline']['difficulty_average_score'][difficulty]} | "
            f"{summaries['lora_v1']['difficulty_average_score'][difficulty]} | "
            f"{summaries['lora_v2']['difficulty_average_score'][difficulty]} |"
        )

    lines.extend([
        "",
        "## Delta Summary",
        "",
        f"- LoRA v1 vs baseline overall delta: {comparison['overall_delta']['lora_v1_minus_baseline']}",
        f"- LoRA v2 vs LoRA v1 overall delta: {comparison['overall_delta']['lora_v2_minus_lora_v1']}",
        f"- LoRA v2 vs baseline overall delta: {comparison['overall_delta']['lora_v2_minus_baseline']}",
        "",
        "## Important Reminder",
        "",
        "This rubric is intentionally simple and keyword-driven. It is useful for trend screening, but it cannot replace manual review or LLM-as-a-judge evaluation for nuanced customer-service quality.",
    ])
    MARKDOWN_OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows_by_model = {model: read_jsonl(path) for model, path in SCORE_PATHS.items()}
    validate_alignment(rows_by_model)
    summaries = {model: summarize(rows) for model, rows in rows_by_model.items()}
    comparison = {
        "summaries": summaries,
        "best_by_category": best_by_category(summaries),
        "overall_delta": {
            "lora_v1_minus_baseline": round(
                summaries["lora_v1"]["overall_average_score"] - summaries["baseline"]["overall_average_score"], 3
            ),
            "lora_v2_minus_lora_v1": round(
                summaries["lora_v2"]["overall_average_score"] - summaries["lora_v1"]["overall_average_score"], 3
            ),
            "lora_v2_minus_baseline": round(
                summaries["lora_v2"]["overall_average_score"] - summaries["baseline"]["overall_average_score"], 3
            ),
        },
        "category_delta": {
            "lora_v1_minus_baseline": delta_map(
                summaries["baseline"]["category_average_score"],
                summaries["lora_v1"]["category_average_score"],
            ),
            "lora_v2_minus_lora_v1": delta_map(
                summaries["lora_v1"]["category_average_score"],
                summaries["lora_v2"]["category_average_score"],
            ),
            "lora_v2_minus_baseline": delta_map(
                summaries["baseline"]["category_average_score"],
                summaries["lora_v2"]["category_average_score"],
            ),
        },
    }
    JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT_PATH.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(summaries, comparison)
    print(f"Comparison JSON saved to: {JSON_OUTPUT_PATH}")
    print(f"Comparison Markdown saved to: {MARKDOWN_OUTPUT_PATH}")
    print("Eval score comparison v3 completed.")


if __name__ == "__main__":
    main()
