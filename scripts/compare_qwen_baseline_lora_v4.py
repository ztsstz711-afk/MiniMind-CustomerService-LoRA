"""Compare Qwen baseline and Qwen LoRA v4 rule-based eval scores."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "outputs" / "eval_scores_qwen_baseline_v4.jsonl"
LORA_PATH = PROJECT_ROOT / "outputs" / "eval_scores_qwen_lora_v4.jsonl"
JSON_OUTPUT = PROJECT_ROOT / "outputs" / "qwen_baseline_lora_comparison_v4.json"
REPORT_OUTPUT = PROJECT_ROOT / "experiments" / "qwen_baseline_lora_comparison_v4.md"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def grouped_average(rows: list[dict], field: str) -> dict[str, float]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[field]].append(float(row["total_score"]))
    return {key: round(mean(values), 3) for key, values in sorted(grouped.items())}


def summarize(rows: list[dict]) -> dict:
    refusal_rows = [row for row in rows if row["category"] == "拒绝不合理请求"]
    unsafe_count = sum(1 for row in rows if row["flags"].get("unsafe_promise"))
    repetition_count = sum(1 for row in rows if row["flags"].get("severe_repetition"))
    length_count = sum(1 for row in rows if row["flags"].get("too_short") or row["flags"].get("too_long"))
    return {
        "overall_average": round(mean(float(row["total_score"]) for row in rows), 3),
        "category_average": grouped_average(rows, "category"),
        "difficulty_average": grouped_average(rows, "difficulty"),
        "refusal_category_average": round(mean(float(row["total_score"]) for row in refusal_rows), 3),
        "refusal_present_count": sum(1 for row in refusal_rows if row["flags"].get("refusal_present")),
        "refusal_total": len(refusal_rows),
        "unsafe_flags_count": unsafe_count,
        "repetition_penalty_count": repetition_count,
        "length_penalty_count": length_count,
    }


def delta_map(after: dict[str, float], before: dict[str, float]) -> dict[str, float]:
    keys = sorted(set(after) | set(before))
    return {key: round(after.get(key, 0.0) - before.get(key, 0.0), 3) for key in keys}


def main() -> None:
    baseline = read_jsonl(BASELINE_PATH)
    lora = read_jsonl(LORA_PATH)
    if len(baseline) != len(lora):
        raise ValueError(f"Length mismatch: baseline {len(baseline)} vs lora {len(lora)}")
    for index, (base_row, lora_row) in enumerate(zip(baseline, lora), start=1):
        for field in ("id", "category", "prompt"):
            if base_row[field] != lora_row[field]:
                raise ValueError(f"{field} mismatch at row {index}")

    baseline_summary = summarize(baseline)
    lora_summary = summarize(lora)
    comparison = {
        "baseline": baseline_summary,
        "qwen_lora_v4": lora_summary,
        "overall_delta_lora_minus_baseline": round(
            lora_summary["overall_average"] - baseline_summary["overall_average"], 3
        ),
        "category_delta_lora_minus_baseline": delta_map(
            lora_summary["category_average"], baseline_summary["category_average"]
        ),
        "difficulty_delta_lora_minus_baseline": delta_map(
            lora_summary["difficulty_average"], baseline_summary["difficulty_average"]
        ),
    }

    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Qwen Baseline vs Qwen LoRA v4 Comparison",
        "",
        "## Overall",
        "",
        "| model | overall_avg | refusal_avg | unsafe_flags | repetition_penalty | length_penalty |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| Qwen baseline | {baseline_summary['overall_average']} | "
            f"{baseline_summary['refusal_category_average']} | {baseline_summary['unsafe_flags_count']} | "
            f"{baseline_summary['repetition_penalty_count']} | {baseline_summary['length_penalty_count']} |"
        ),
        (
            f"| Qwen LoRA v4 | {lora_summary['overall_average']} | "
            f"{lora_summary['refusal_category_average']} | {lora_summary['unsafe_flags_count']} | "
            f"{lora_summary['repetition_penalty_count']} | {lora_summary['length_penalty_count']} |"
        ),
        "",
        f"- overall delta (LoRA - baseline): {comparison['overall_delta_lora_minus_baseline']}",
        (
            "- 判断：如果 LoRA 分数下降或重复惩罚增加，说明极低训练 loss 可能对应过拟合、"
            "模板化或训练数据分布过窄，而不一定代表业务质量提升。"
        ),
        "",
        "## Category Average",
        "",
        "| category | baseline | qwen_lora_v4 | delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category, baseline_score in baseline_summary["category_average"].items():
        lora_score = lora_summary["category_average"].get(category, 0.0)
        delta = comparison["category_delta_lora_minus_baseline"][category]
        lines.append(f"| {category} | {baseline_score} | {lora_score} | {delta} |")

    lines.extend([
        "",
        "## Difficulty Average",
        "",
        "| difficulty | baseline | qwen_lora_v4 | delta |",
        "| --- | ---: | ---: | ---: |",
    ])
    for difficulty, baseline_score in baseline_summary["difficulty_average"].items():
        lora_score = lora_summary["difficulty_average"].get(difficulty, 0.0)
        delta = comparison["difficulty_delta_lora_minus_baseline"][difficulty]
        lines.append(f"| {difficulty} | {baseline_score} | {lora_score} | {delta} |")

    lines.extend([
        "",
        "## Key Notes",
        "",
        "- 本报告使用 rule-based rubric，只能作为粗粒度自动评估。",
        "- 需要结合人工阅读判断：LoRA 是否更合规，是否更像售后客服，是否出现模板化和过拟合。",
        "- 下一步可扩展到 LLM-as-a-judge 或人工 rubrics 复评。",
    ])
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Baseline overall: {baseline_summary['overall_average']}")
    print(f"Qwen LoRA v4 overall: {lora_summary['overall_average']}")
    print(f"Overall delta: {comparison['overall_delta_lora_minus_baseline']}")
    print(f"Baseline refusal average: {baseline_summary['refusal_category_average']}")
    print(f"Qwen LoRA v4 refusal average: {lora_summary['refusal_category_average']}")
    print(f"Baseline unsafe flags: {baseline_summary['unsafe_flags_count']}")
    print(f"Qwen LoRA v4 unsafe flags: {lora_summary['unsafe_flags_count']}")
    print(f"JSON saved to: {JSON_OUTPUT}")
    print(f"Markdown saved to: {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
