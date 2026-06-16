"""Compare baseline, LoRA v1, and LoRA v2 outputs on fixed prompts."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "outputs" / "baseline_outputs.jsonl"
LORA_V1_PATH = PROJECT_ROOT / "outputs" / "lora_outputs.jsonl"
LORA_V2_PATH = PROJECT_ROOT / "outputs" / "lora_v2_outputs.jsonl"
JSONL_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "baseline_lora_v1_v2_comparison.jsonl"
MARKDOWN_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "baseline_lora_v1_v2_comparison.md"

KEYWORDS = {
    "polite_opening": ("您好", "你好"),
    "appeasement": ("抱歉", "理解", "很抱歉", "不便", "着急"),
    "asks_info": ("订单号", "提供", "截图", "信息", "联系方式", "核实"),
    "rule_explanation": ("规则", "平台", "通常", "需要", "根据", "无法", "不能", "不支持"),
    "next_step": ("建议", "请您", "可以", "帮您", "处理", "申请", "查询", "提交"),
    "refusal": ("无法", "不能", "不支持", "不符合规则", "很抱歉"),
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
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


def has_repetition(text: str) -> bool:
    if re.search(r"(.{2,16})\1{3,}", text):
        return True
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    counts = {}
    for chunk in chunks:
        counts[chunk] = counts.get(chunk, 0) + 1
    return any(count >= 10 for count in counts.values())


def score(text: str, category: str) -> dict[str, bool]:
    stripped = text.strip()
    result = {
        name: any(keyword in stripped for keyword in keywords)
        for name, keywords in KEYWORDS.items()
    }
    result["is_empty"] = not bool(stripped)
    result["too_short"] = 0 < len(stripped) < 12
    result["has_repetition"] = has_repetition(stripped)
    result["invalid_request_refused"] = (
        category != "拒绝不合理请求" or result["refusal"]
    )
    return result


def validate_alignment(*record_sets: list[dict]) -> None:
    names = ("baseline", "lora_v1", "lora_v2")
    for name, records in zip(names, record_sets):
        if len(records) != 10:
            raise ValueError(f"Expected 10 {name} records, got {len(records)}")

    for index, rows in enumerate(zip(*record_sets), start=1):
        categories = {row.get("category") for row in rows}
        prompts = {row.get("prompt") for row in rows}
        if len(categories) != 1:
            raise ValueError(f"Category mismatch at row {index}: {categories}")
        if len(prompts) != 1:
            raise ValueError(f"Prompt mismatch at row {index}")
        for name, row in zip(names, rows):
            if "model_output" not in row:
                raise ValueError(f"Missing model_output in {name} row {index}")


def summarize_scores(name: str, scores: list[dict]) -> list[str]:
    fields = [
        "polite_opening",
        "appeasement",
        "asks_info",
        "rule_explanation",
        "next_step",
        "refusal",
        "is_empty",
        "too_short",
        "has_repetition",
    ]
    return [f"| {name} | " + " | ".join(str(sum(item[field] for item in scores)) for field in fields) + " |"]


def observe(category: str, base_score: dict, v1_score: dict, v2_score: dict) -> str:
    notes = []
    for field, label in [
        ("polite_opening", "礼貌开头"),
        ("appeasement", "安抚表达"),
        ("asks_info", "必要信息询问"),
        ("rule_explanation", "规则说明"),
        ("next_step", "下一步操作"),
    ]:
        if v2_score[field] and not v1_score[field]:
            notes.append(f"v2 增强了{label}")
        elif v1_score[field] and not v2_score[field]:
            notes.append(f"v2 的{label}弱于 v1")
    if category == "拒绝不合理请求":
        if v2_score["refusal"] and not v1_score["refusal"]:
            notes.append("v2 对不合理请求给出了更明确拒绝")
        elif not v2_score["refusal"]:
            notes.append("v2 仍未稳定给出明确拒绝")
    if v2_score["has_repetition"]:
        notes.append("v2 存在明显重复")
    if v2_score["too_short"] or v2_score["is_empty"]:
        notes.append("v2 输出过短或为空")
    if not notes:
        notes.append("v2 与 v1 在关键词维度接近，需人工进一步判断语义质量")
    return "；".join(notes) + "。"


def write_outputs(records: list[dict]) -> None:
    JSONL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with JSONL_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    baseline_scores = [record["auto_scores"]["baseline"] for record in records]
    v1_scores = [record["auto_scores"]["lora_v1"] for record in records]
    v2_scores = [record["auto_scores"]["lora_v2"] for record in records]
    header_fields = [
        "polite_opening",
        "appeasement",
        "asks_info",
        "rule_explanation",
        "next_step",
        "refusal",
        "is_empty",
        "too_short",
        "has_repetition",
    ]

    lines = [
        "# Baseline vs LoRA v1 vs LoRA v2 Comparison",
        "",
        f"- baseline: `{BASELINE_PATH}`",
        f"- LoRA v1: `{LORA_V1_PATH}`",
        f"- LoRA v2: `{LORA_V2_PATH}`",
        "",
        "## Summary",
        "",
        "| Model | " + " | ".join(header_fields) + " |",
        "| --- | " + " | ".join("---:" for _ in header_fields) + " |",
    ]
    lines.extend(summarize_scores("Baseline", baseline_scores))
    lines.extend(summarize_scores("LoRA v1", v1_scores))
    lines.extend(summarize_scores("LoRA v2", v2_scores))

    lines.extend(["", "## Cases", ""])
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"### {index}. {record['category']}",
                "",
                "**用户问题**",
                "",
                record["prompt"],
                "",
                "**Baseline 回复**",
                "",
                record["baseline_output"],
                "",
                "**LoRA v1 回复**",
                "",
                record["lora_v1_output"],
                "",
                "**LoRA v2 回复**",
                "",
                record["lora_v2_output"],
                "",
                "**简短观察**",
                "",
                record["short_observation"],
                "",
            ]
        )
    MARKDOWN_OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    baseline = read_jsonl(BASELINE_PATH)
    lora_v1 = read_jsonl(LORA_V1_PATH)
    lora_v2 = read_jsonl(LORA_V2_PATH)
    validate_alignment(baseline, lora_v1, lora_v2)

    records = []
    for base, v1, v2 in zip(baseline, lora_v1, lora_v2):
        category = base["category"]
        baseline_output = str(base["model_output"])
        v1_output = str(v1["model_output"])
        v2_output = str(v2["model_output"])
        auto_scores = {
            "baseline": score(baseline_output, category),
            "lora_v1": score(v1_output, category),
            "lora_v2": score(v2_output, category),
        }
        records.append(
            {
                "category": category,
                "prompt": base["prompt"],
                "baseline_output": baseline_output,
                "lora_v1_output": v1_output,
                "lora_v2_output": v2_output,
                "short_observation": observe(
                    category,
                    auto_scores["baseline"],
                    auto_scores["lora_v1"],
                    auto_scores["lora_v2"],
                ),
                "auto_scores": auto_scores,
            }
        )

    write_outputs(records)
    print(f"Comparison cases: {len(records)}")
    print("Alignment: OK")
    print(f"Markdown saved to: {MARKDOWN_OUTPUT_PATH}")
    print(f"JSONL saved to: {JSONL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
