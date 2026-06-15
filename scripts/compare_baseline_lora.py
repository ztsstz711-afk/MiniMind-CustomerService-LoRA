"""Compare MiniMind baseline and LoRA outputs on fixed customer-service prompts."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "outputs" / "baseline_outputs.jsonl"
LORA_PATH = PROJECT_ROOT / "outputs" / "lora_outputs.jsonl"
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"
JSONL_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "before_after_comparison.jsonl"
MARKDOWN_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "before_after_comparison.md"

KEYWORDS = {
    "has_polite_apology": ("您好", "抱歉", "理解", "很抱歉"),
    "asks_for_order_id_or_info": ("订单号", "提供", "信息", "截图", "联系方式"),
    "explains_rule": ("规则", "平台", "通常", "无法", "需要", "根据"),
    "gives_next_step": ("建议", "可以", "请您", "帮您", "处理", "查询", "申请"),
    "refuses_invalid_request": ("无法", "不能", "不支持", "不符合规则", "很抱歉"),
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


def has_obvious_repetition(text: str) -> bool:
    if not text.strip():
        return False
    repeated_phrases = re.findall(r"(.{2,12}?)(?:\1){2,}", text)
    if repeated_phrases:
        return True
    words = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    if not words:
        return False
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return any(count >= 8 for count in counts.values())


def score_output(text: str) -> dict[str, bool]:
    stripped = text.strip()
    fields = {
        name: any(keyword in stripped for keyword in keywords)
        for name, keywords in KEYWORDS.items()
    }
    fields["has_obvious_repetition"] = has_obvious_repetition(stripped)
    fields["is_empty"] = not bool(stripped)
    return fields


def validate_alignment(prompts: list[dict], baseline: list[dict], lora: list[dict]) -> None:
    if len(prompts) != 10:
        raise ValueError(f"Expected 10 baseline prompts, got {len(prompts)}")
    if len(baseline) != 10:
        raise ValueError(f"Expected 10 baseline outputs, got {len(baseline)}")
    if len(lora) != 10:
        raise ValueError(f"Expected 10 LoRA outputs, got {len(lora)}")

    for index, (prompt, base, lora_record) in enumerate(zip(prompts, baseline, lora), start=1):
        for record_name, record in (("prompt", prompt), ("baseline", base), ("lora", lora_record)):
            missing = {"category", "prompt"} - set(record)
            if missing:
                raise ValueError(f"{record_name} record {index} missing fields: {sorted(missing)}")
        if prompt["category"] != base["category"] or base["category"] != lora_record["category"]:
            raise ValueError(f"Category mismatch at row {index}")
        if prompt["prompt"] != base["prompt"] or base["prompt"] != lora_record["prompt"]:
            raise ValueError(f"Prompt mismatch at row {index}")
        if "model_output" not in base or "model_output" not in lora_record:
            raise ValueError(f"Missing model_output at row {index}")


def write_outputs(records: list[dict]) -> None:
    JSONL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with JSONL_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    lines = [
        "# Baseline vs LoRA Before/After Comparison",
        "",
        f"- baseline: `{BASELINE_PATH}`",
        f"- lora: `{LORA_PATH}`",
        f"- prompts: `{PROMPTS_PATH}`",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | LoRA |",
        "| --- | ---: | ---: |",
    ]
    for field in [
        "has_polite_apology",
        "asks_for_order_id_or_info",
        "explains_rule",
        "gives_next_step",
        "refuses_invalid_request",
        "has_obvious_repetition",
        "is_empty",
    ]:
        base_count = sum(record["manual_score_fields"]["baseline"][field] for record in records)
        lora_count = sum(record["manual_score_fields"]["lora"][field] for record in records)
        lines.append(f"| `{field}` | {base_count} | {lora_count} |")

    lines.extend(["", "## Details", ""])
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"### {index}. {record['category']}",
                "",
                "**Prompt**",
                "",
                record["prompt"],
                "",
                "**Baseline Output**",
                "",
                record["baseline_output"],
                "",
                "**LoRA Output**",
                "",
                record["lora_output"],
                "",
                "**Auto Score**",
                "",
                "```json",
                json.dumps(record["manual_score_fields"], ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    MARKDOWN_OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    prompts = read_jsonl(PROMPTS_PATH)
    baseline = read_jsonl(BASELINE_PATH)
    lora = read_jsonl(LORA_PATH)
    validate_alignment(prompts, baseline, lora)

    records = []
    for base, lora_record in zip(baseline, lora):
        baseline_output = str(base["model_output"])
        lora_output = str(lora_record["model_output"])
        records.append(
            {
                "category": base["category"],
                "prompt": base["prompt"],
                "baseline_output": baseline_output,
                "lora_output": lora_output,
                "manual_score_fields": {
                    "baseline": score_output(baseline_output),
                    "lora": score_output(lora_output),
                },
            }
        )

    write_outputs(records)
    print(f"Baseline outputs: {len(baseline)}")
    print(f"LoRA outputs: {len(lora)}")
    print("Alignment: OK")
    print(f"Markdown saved to: {MARKDOWN_OUTPUT_PATH}")
    print(f"JSONL saved to: {JSONL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
