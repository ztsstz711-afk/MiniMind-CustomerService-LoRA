"""Inspect downloaded real customer-service data for v5.

This script does not train or modify data. It prints basic structure so the
JDDC conversion script can be adapted to the actual downloaded format.
"""

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect real customer-service data files.")
    parser.add_argument("--data_path", type=Path, required=True, help="Path to json/jsonl/txt data file.")
    return parser.parse_args()


def preview(value: Any, limit: int = 500) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value
    return text[:limit] + ("..." if len(text) > limit else "")


def inspect_json(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"Detected format: json")
    print(f"Top-level type: {type(data).__name__}")
    if isinstance(data, dict):
        print(f"Top-level fields: {sorted(data.keys())}")
        candidate = None
        for value in data.values():
            if isinstance(value, list) and value:
                candidate = value
                break
        samples = candidate[:3] if isinstance(candidate, list) else [data]
    elif isinstance(data, list):
        samples = data[:3]
    else:
        samples = [data]
    for index, sample in enumerate(samples, start=1):
        print(f"\nSample {index}:")
        if isinstance(sample, dict):
            print(f"Fields: {sorted(sample.keys())}")
        print(preview(sample))


def inspect_jsonl(path: Path) -> None:
    print("Detected format: jsonl")
    samples = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                samples.append(json.loads(line))
            if len(samples) >= 3:
                break
    for index, sample in enumerate(samples, start=1):
        print(f"\nSample {index}:")
        if isinstance(sample, dict):
            print(f"Fields: {sorted(sample.keys())}")
        print(preview(sample))


def inspect_txt(path: Path) -> None:
    print("Detected format: txt")
    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    non_empty = [line for line in lines if line.strip()]
    print(f"Total lines: {len(lines)}")
    print(f"Non-empty lines: {len(non_empty)}")
    for index, line in enumerate(non_empty[:3], start=1):
        print(f"\nSample {index}:")
        print(preview(line))


def main() -> None:
    args = parse_args()
    path = args.data_path
    if not path.is_file():
        raise FileNotFoundError(f"Missing data file: {path}")
    print(f"Data path: {path}")
    print(f"File size bytes: {path.stat().st_size}")
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        inspect_jsonl(path)
    elif suffix == ".json":
        inspect_json(path)
    elif suffix in {".txt", ".csv", ".tsv"}:
        inspect_txt(path)
    else:
        print(f"Unknown suffix: {suffix}; trying JSONL first, then TXT fallback.")
        try:
            inspect_jsonl(path)
        except Exception as exc:
            print(f"JSONL inspection failed: {exc}")
            inspect_txt(path)
    print("Real data v5 inspection completed.")


if __name__ == "__main__":
    main()
