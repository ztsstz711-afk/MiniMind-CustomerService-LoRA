"""Check LoRA v2 inference outputs against the fixed baseline prompts."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"
JSONL_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "lora_v2_outputs.jsonl"
MARKDOWN_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "lora_v2_outputs.md"


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
    if re.search(r"(.{2,16})\1{3,}", text):
        return True
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    counts = {}
    for chunk in chunks:
        counts[chunk] = counts.get(chunk, 0) + 1
    return any(count >= 10 for count in counts.values())


def looks_garbled(text: str) -> bool:
    if not text:
        return False
    replacement_count = text.count("\ufffd")
    ascii_symbols = sum(1 for char in text if ord(char) < 32 and char not in "\n\t")
    return replacement_count > 0 or ascii_symbols > 0


def main() -> None:
    prompts = read_jsonl(PROMPTS_PATH)
    outputs = read_jsonl(JSONL_OUTPUT_PATH)
    if not MARKDOWN_OUTPUT_PATH.is_file():
        raise FileNotFoundError(f"Missing markdown output: {MARKDOWN_OUTPUT_PATH}")

    if len(prompts) != 10:
        raise ValueError(f"Expected 10 prompts, got {len(prompts)}")
    if len(outputs) != 10:
        raise ValueError(f"Expected 10 LoRA v2 outputs, got {len(outputs)}")

    empty_outputs = []
    short_outputs = []
    repeated_outputs = []
    garbled_outputs = []
    exact_duplicate_outputs = {}

    for index, (prompt, output) in enumerate(zip(prompts, outputs), start=1):
        for field in ("category", "prompt"):
            if prompt.get(field) != output.get(field):
                raise ValueError(f"{field} mismatch at row {index}")
        model_output = str(output.get("model_output", "")).strip()
        if not model_output:
            empty_outputs.append(index)
        if len(model_output) < 8:
            short_outputs.append(index)
        if has_obvious_repetition(model_output):
            repeated_outputs.append(index)
        if looks_garbled(model_output):
            garbled_outputs.append(index)
        exact_duplicate_outputs.setdefault(model_output, []).append(index)

    duplicates = {
        text: indexes
        for text, indexes in exact_duplicate_outputs.items()
        if text and len(indexes) > 1
    }

    print(f"LoRA v2 outputs: {len(outputs)}")
    print(f"Markdown found: {MARKDOWN_OUTPUT_PATH}")
    print(f"Empty outputs: {empty_outputs if empty_outputs else 'none'}")
    print(f"Very short outputs: {short_outputs if short_outputs else 'none'}")
    print(f"Repeated outputs: {repeated_outputs if repeated_outputs else 'none'}")
    print(f"Garbled outputs: {garbled_outputs if garbled_outputs else 'none'}")
    print(f"Exact duplicate outputs: {duplicates if duplicates else 'none'}")

    if empty_outputs:
        raise ValueError(f"Empty LoRA v2 outputs at rows: {empty_outputs}")
    if garbled_outputs:
        raise ValueError(f"Garbled LoRA v2 outputs at rows: {garbled_outputs}")
    if duplicates:
        raise ValueError(f"Duplicate LoRA v2 outputs found: {duplicates}")

    print("LoRA v2 inference output check completed.")


if __name__ == "__main__":
    main()
