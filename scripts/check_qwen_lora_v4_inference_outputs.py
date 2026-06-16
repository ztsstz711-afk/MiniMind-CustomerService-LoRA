"""Check Qwen LoRA v4 eval inference outputs."""

import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"
JSONL_PATH = PROJECT_ROOT / "outputs" / "eval_outputs_qwen_lora_v4.jsonl"
MARKDOWN_PATH = PROJECT_ROOT / "experiments" / "eval_outputs_qwen_lora_v4.md"
LEAK_PATTERNS = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手",
    '"messages"',
    '"instruction"',
    '"output"',
    '"category"',
    "required_elements",
    "forbidden_elements",
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def has_repetition(text: str) -> bool:
    if re.search(r"(.{2,18})\1{3,}", text):
        return True
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    counts = Counter(chunks)
    return any(count >= 10 for count in counts.values())


def looks_garbled(text: str) -> bool:
    return "\ufffd" in text or any(ord(ch) < 32 and ch not in "\n\t" for ch in text)


def has_template_leak(text: str) -> bool:
    return any(pattern in text for pattern in LEAK_PATTERNS)


def main() -> None:
    eval_rows = read_jsonl(EVAL_PATH)
    output_rows = read_jsonl(JSONL_PATH)
    if not MARKDOWN_PATH.is_file():
        raise FileNotFoundError(f"Missing markdown output: {MARKDOWN_PATH}")
    if len(eval_rows) != 100:
        raise ValueError(f"Expected 100 eval prompts, got {len(eval_rows)}")
    if len(output_rows) != 100:
        raise ValueError(f"Expected 100 outputs, got {len(output_rows)}")

    empty_rows = []
    short_rows = []
    repeated_rows = []
    garbled_rows = []
    leak_rows = []
    for index, (eval_row, output_row) in enumerate(zip(eval_rows, output_rows), start=1):
        for field in ("id", "category", "prompt"):
            if eval_row[field] != output_row.get(field):
                raise ValueError(f"{field} mismatch at row {index}")
        output = str(output_row.get("output", "")).strip()
        if not output:
            empty_rows.append(index)
        if 0 < len(output) < 20:
            short_rows.append(index)
        if has_repetition(output):
            repeated_rows.append(index)
        if looks_garbled(output):
            garbled_rows.append(index)
        if has_template_leak(output):
            leak_rows.append(index)

    print(f"Qwen LoRA v4 outputs: {len(output_rows)}")
    print(f"JSONL output: {JSONL_PATH}")
    print(f"Markdown output: {MARKDOWN_PATH}")
    print(f"Empty outputs: {len(empty_rows)}")
    print(f"Very short outputs: {len(short_rows)}")
    print(f"Repeated output rows: {len(repeated_rows)}")
    print(f"Repeated output row indexes: {repeated_rows[:20] if repeated_rows else 'none'}")
    print(f"Garbled outputs: {len(garbled_rows)}")
    print(f"Garbled output row indexes: {garbled_rows[:20] if garbled_rows else 'none'}")
    print(f"Template leak rows: {len(leak_rows)}")
    print(f"Template leak row indexes: {leak_rows[:20] if leak_rows else 'none'}")
    if empty_rows:
        raise ValueError(f"Empty outputs at rows: {empty_rows[:20]}")
    print("Qwen LoRA v4 inference output check completed.")


if __name__ == "__main__":
    main()
