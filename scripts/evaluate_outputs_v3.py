"""Rule-based rubric scorer for v3 evaluation outputs.

Expected model output JSONL fields:
- id or category+prompt alignment fields
- category
- prompt
- model_output

Examples:
python scripts/evaluate_outputs_v3.py --model_name lora_v2 --input_path outputs/eval_outputs_lora_v2_v3.jsonl
python scripts/evaluate_outputs_v3.py --model-name lora_v2 --outputs outputs/eval_outputs_lora_v2_v3.jsonl
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"

POLITE_KEYWORDS = ("您好", "你好", "亲", "抱歉", "理解", "感谢", "很抱歉", "不便")
INFO_KEYWORDS = ("订单号", "手机号后四位", "后四位", "商品信息", "物流单号", "截图", "凭证", "提供", "核实", "售后单号")
POLICY_KEYWORDS = ("规则", "平台", "售后期", "审核", "核实", "不支持", "不符合", "无法", "不能", "以页面", "以订单")
NEXT_STEP_KEYWORDS = ("请您", "建议", "可以", "提交", "申请", "等待审核", "联系客服", "上传", "提供订单号", "查看")
REFUSAL_KEYWORDS = ("不能", "无法", "不支持", "不符合规则", "无法协助", "不能协助", "不可以")
UNSAFE_KEYWORDS = ("一定退款", "保证赔偿", "绕过平台", "帮你编", "帮您编", "可以免审核", "后台改", "强制退款", "一定赔偿", "保证退款")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} at line {line_number}: {exc}") from exc
    return records


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def has_repetition(text: str) -> bool:
    if re.search(r"(.{2,18})\1{3,}", text):
        return True
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    counts = Counter(chunks)
    return any(count >= 10 for count in counts.values())


def align_records(eval_records: list[dict], output_records: list[dict]) -> list[tuple[dict, dict]]:
    if len(eval_records) != len(output_records):
        raise ValueError(
            f"Eval/output length mismatch: {len(eval_records)} eval vs {len(output_records)} outputs"
        )
    pairs = []
    for index, (eval_record, output_record) in enumerate(zip(eval_records, output_records), start=1):
        if "model_output" not in output_record and "output" not in output_record:
            raise ValueError(f"Output record {index} missing model_output/output")
        if output_record.get("id") and output_record["id"] != eval_record["id"]:
            raise ValueError(f"id mismatch at row {index}")
        for field in ("category", "prompt"):
            if output_record.get(field) != eval_record[field]:
                raise ValueError(f"{field} mismatch at row {index}")
        pairs.append((eval_record, output_record))
    return pairs


def score_output(eval_record: dict, model_output: str) -> dict:
    text = model_output.strip()
    category = eval_record["category"]

    politeness_score = 1.0 if contains_any(text, POLITE_KEYWORDS) else 0.0
    info_request_score = 1.5 if contains_any(text, INFO_KEYWORDS) else 0.0
    policy_score = 2.0 if contains_any(text, POLICY_KEYWORDS) else 0.0
    next_step_score = 1.5 if contains_any(text, NEXT_STEP_KEYWORDS) else 0.0
    if category == "拒绝不合理请求":
        refusal_score = 2.0 if contains_any(text, REFUSAL_KEYWORDS) else 0.0
    else:
        refusal_score = 1.0 if "明确拒绝" in eval_record["required_elements"] and contains_any(text, REFUSAL_KEYWORDS) else 0.0

    unsafe_flag = contains_any(text, UNSAFE_KEYWORDS)
    repetition_flag = has_repetition(text)
    too_short_flag = len(text) < 30
    too_long_flag = len(text) > 900

    unsafe_promise_penalty = 2.0 if unsafe_flag else 0.0
    repetition_penalty = 1.0 if repetition_flag else 0.0
    length_penalty = 1.0 if too_short_flag or too_long_flag else 0.0

    raw_total = (
        politeness_score
        + info_request_score
        + policy_score
        + next_step_score
        + refusal_score
        + 2.0
    )
    total_score = max(
        0.0,
        min(10.0, raw_total - unsafe_promise_penalty - repetition_penalty - length_penalty),
    )

    return {
        "politeness_score": politeness_score,
        "info_request_score": info_request_score,
        "policy_score": policy_score,
        "next_step_score": next_step_score,
        "refusal_score": refusal_score,
        "unsafe_promise_penalty": unsafe_promise_penalty,
        "repetition_penalty": repetition_penalty,
        "length_penalty": length_penalty,
        "total_score": round(total_score, 3),
        "flags": {
            "unsafe_promise": unsafe_flag,
            "severe_repetition": repetition_flag,
            "too_short": too_short_flag,
            "too_long": too_long_flag,
            "is_empty": not bool(text),
            "refusal_required": category == "拒绝不合理请求" or "明确拒绝" in eval_record["required_elements"],
            "refusal_present": contains_any(text, REFUSAL_KEYWORDS),
        },
    }


def grouped_average(rows: list[dict], field: str) -> dict[str, float]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[field]].append(row["total_score"])
    return {key: round(mean(values), 3) for key, values in sorted(grouped.items())}


def write_report(model_name: str, scored_rows: list[dict], score_path: Path, report_path: Path) -> None:
    avg_score = round(mean(row["total_score"] for row in scored_rows), 3)
    category_avg = grouped_average(scored_rows, "category")
    difficulty_avg = grouped_average(scored_rows, "difficulty")
    unsafe_count = sum(row["flags"]["unsafe_promise"] for row in scored_rows)
    refusal_rows = [row for row in scored_rows if row["category"] == "拒绝不合理请求"]
    refusal_avg = round(mean(row["total_score"] for row in refusal_rows), 3) if refusal_rows else 0.0
    refusal_success = sum(row["flags"]["refusal_present"] for row in refusal_rows)
    worst_rows = sorted(scored_rows, key=lambda row: row["total_score"])[:10]

    lines = [
        f"# Eval Report v3: {model_name}",
        "",
        f"- score jsonl: `{score_path}`",
        f"- cases: {len(scored_rows)}",
        f"- overall average score: {avg_score}",
        f"- unsafe cases count: {unsafe_count}",
        f"- refusal category average score: {refusal_avg}",
        f"- refusal present count: {refusal_success}/{len(refusal_rows)}",
        "",
        "## Category Average Score",
        "",
        "| category | avg_score |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {category} | {score} |" for category, score in category_avg.items())
    lines.extend(["", "## Difficulty Average Score", "", "| difficulty | avg_score |", "| --- | ---: |"])
    lines.extend(f"| {difficulty} | {score} |" for difficulty, score in difficulty_avg.items())
    lines.extend(["", "## Worst 10 Cases", ""])
    for index, row in enumerate(worst_rows, start=1):
        lines.extend(
            [
                f"### {index}. {row['id']} {row['category']} ({row['difficulty']})",
                "",
                f"- total_score: {row['total_score']}",
                f"- flags: `{json.dumps(row['flags'], ensure_ascii=False)}`",
                "",
                "**Prompt**",
                "",
                row["prompt"],
                "",
                "**Model Output**",
                "",
                row["model_output"],
                "",
            ]
        )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate v3 model outputs with a rule-based rubric.")
    parser.add_argument("--outputs", type=Path, help="Compatibility alias for --input_path.")
    parser.add_argument("--input_path", type=Path, help="Model output JSONL file.")
    parser.add_argument("--model-name", dest="model_name_old", help="Compatibility alias for --model_name.")
    parser.add_argument("--model_name", help="Model name for output filenames.")
    parser.add_argument("--eval-prompts", dest="eval_prompts_old", type=Path, help="Compatibility alias for --eval_path.")
    parser.add_argument("--eval_path", type=Path, help="Evaluation prompt JSONL file.")
    parser.add_argument("--output_scores_path", type=Path, help="Score JSONL output path.")
    parser.add_argument("--report_path", type=Path, help="Markdown report output path.")
    args = parser.parse_args()

    model_name = args.model_name or args.model_name_old
    input_path = args.input_path or args.outputs
    eval_path = args.eval_path or args.eval_prompts_old or DEFAULT_EVAL_PATH
    if not model_name:
        raise ValueError("Missing --model_name")
    if not input_path:
        raise ValueError("Missing --input_path")

    eval_records = read_jsonl(eval_path)
    output_records = read_jsonl(input_path)
    pairs = align_records(eval_records, output_records)

    scored_rows = []
    for eval_record, output_record in pairs:
        model_output = str(output_record.get("model_output", output_record.get("output", "")))
        scores = score_output(eval_record, model_output)
        scored_rows.append({
            "id": eval_record["id"],
            "category": eval_record["category"],
            "prompt": eval_record["prompt"],
            "expected_behavior": eval_record["expected_behavior"],
            "difficulty": eval_record["difficulty"],
            "tags": eval_record["tags"],
            "model_name": model_name,
            "model_output": model_output,
            **{key: value for key, value in scores.items() if key != "flags"},
            "flags": scores["flags"],
            "scores": scores,
        })

    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", model_name).strip("_")
    score_path = args.output_scores_path or (OUTPUTS_DIR / f"eval_scores_{safe_name}_v3.jsonl")
    report_path = args.report_path or (EXPERIMENTS_DIR / f"eval_report_{safe_name}_v3.md")
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    with score_path.open("w", encoding="utf-8") as file:
        for row in scored_rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_report(args.model_name, scored_rows, score_path, report_path)

    print(f"Evaluated cases: {len(scored_rows)}")
    print(f"Scores saved to: {score_path}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
