"""Check v3 evaluation inference outputs for one model."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PROMPTS_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"
MODEL_NAMES = ("baseline", "lora_v1", "lora_v2")


def output_paths(model_name: str) -> tuple[Path, Path]:
    return (
        PROJECT_ROOT / "outputs" / f"eval_outputs_{model_name}_v3.jsonl",
        PROJECT_ROOT / "experiments" / f"eval_outputs_{model_name}_v3.md",
    )


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
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


def has_repetition(text: str) -> bool:
    if re.search(r"(.{2,18})\1{3,}", text):
        return True
    chunks = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    counts = Counter(chunks)
    return any(count >= 10 for count in counts.values())


def looks_garbled(text: str) -> bool:
    if "\ufffd" in text:
        return True
    control_chars = [char for char in text if ord(char) < 32 and char not in "\n\t"]
    return bool(control_chars)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check v3 evaluation inference outputs.")
    parser.add_argument("--model_name", required=True, choices=MODEL_NAMES)
    args = parser.parse_args()

    jsonl_path, markdown_path = output_paths(args.model_name)
    eval_rows = read_jsonl(EVAL_PROMPTS_PATH)
    output_rows = read_jsonl(jsonl_path)
    if not markdown_path.is_file():
        raise FileNotFoundError(f"Missing markdown output: {markdown_path}")

    if len(eval_rows) != 100:
        raise ValueError(f"Expected 100 eval prompts, got {len(eval_rows)}")
    if len(output_rows) != 100:
        raise ValueError(f"Expected 100 outputs, got {len(output_rows)}")

    empty_rows = []
    short_rows = []
    repeated_rows = []
    garbled_rows = []
    exact_outputs = Counter()

    for index, (eval_row, output_row) in enumerate(zip(eval_rows, output_rows), start=1):
        for field in ("id", "category", "prompt"):
            if eval_row[field] != output_row.get(field):
                raise ValueError(f"{field} mismatch at row {index}")
        if output_row.get("model_name") != args.model_name:
            raise ValueError(f"model_name mismatch at row {index}")
        output = str(output_row.get("output", "")).strip()
        compat_output = str(output_row.get("model_output", "")).strip()
        if output != compat_output:
            raise ValueError(f"output/model_output mismatch at row {index}")
        if not output:
            empty_rows.append(index)
        if 0 < len(output) < 20:
            short_rows.append(index)
        if has_repetition(output):
            repeated_rows.append(index)
        if looks_garbled(output):
            garbled_rows.append(index)
        exact_outputs[output] += 1

    duplicate_count = sum(1 for text, count in exact_outputs.items() if text and count > 1)
    duplicate_rows = sum(count for text, count in exact_outputs.items() if text and count > 1)

    print(f"Model name: {args.model_name}")
    print(f"JSONL output: {jsonl_path}")
    print(f"Markdown output: {markdown_path}")
    print(f"Output rows: {len(output_rows)}")
    print(f"Empty outputs: {len(empty_rows)}")
    print(f"Very short outputs: {len(short_rows)}")
    print(f"Repeated output rows: {len(repeated_rows)}")
    print(f"Repeated output row indexes: {repeated_rows[:20] if repeated_rows else 'none'}")
    print(f"Exact duplicate output groups: {duplicate_count}")
    print(f"Exact duplicate output rows: {duplicate_rows}")
    print(f"Garbled outputs: {len(garbled_rows)}")
    print(f"Garbled output row indexes: {garbled_rows[:20] if garbled_rows else 'none'}")
    if empty_rows:
        raise ValueError(f"Empty outputs at rows: {empty_rows[:20]}")
    print("Eval inference v3 output check completed.")


if __name__ == "__main__":
    main()
