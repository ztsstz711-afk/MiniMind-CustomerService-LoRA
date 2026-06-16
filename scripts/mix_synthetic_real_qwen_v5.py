"""Mix synthetic compliance data with real customer-service data for Qwen v5."""

import argparse
import json
import random
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mix synthetic and real Qwen SFT data for v5.")
    parser.add_argument("--synthetic_path", type=Path, default=PROJECT_ROOT / "data" / "qwen_train_v4.jsonl")
    parser.add_argument("--real_path", type=Path, default=PROJECT_ROOT / "data" / "qwen_real_train_v5.jsonl")
    parser.add_argument("--output_path", type=Path, default=PROJECT_ROOT / "data" / "qwen_train_mixed_v5.jsonl")
    parser.add_argument("--max_real_samples", type=int, default=2000)
    parser.add_argument("--real_ratio", type=float, default=None, help="Optional ratio of real samples in final mix.")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def mark_source(rows: list[dict], source: str) -> list[dict]:
    marked = []
    for row in rows:
        copied = dict(row)
        copied.setdefault("source", source)
        tags = list(copied.get("tags", []))
        if source not in tags:
            tags.append(source)
        copied["tags"] = tags
        marked.append(copied)
    return marked


def choose_real_count(synthetic_count: int, real_count: int, max_real_samples: int, real_ratio: float | None) -> int:
    capped = min(real_count, max_real_samples)
    if real_ratio is None:
        return capped
    if not 0 < real_ratio < 1:
        raise ValueError("--real_ratio must be between 0 and 1")
    target_real = int(round((real_ratio * synthetic_count) / (1 - real_ratio)))
    return min(capped, target_real)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    synthetic = mark_source(read_jsonl(args.synthetic_path), "synthetic_v4")
    real = mark_source(read_jsonl(args.real_path), "real_jddc")
    rng.shuffle(real)
    real_count = choose_real_count(len(synthetic), len(real), args.max_real_samples, args.real_ratio)
    selected_real = real[:real_count]
    mixed = synthetic + selected_real
    rng.shuffle(mixed)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    with args.output_path.open("w", encoding="utf-8") as file:
        for row in mixed:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    source_counts = Counter(row.get("source", "unknown") for row in mixed)
    print(f"Synthetic input: {len(synthetic)}")
    print(f"Real input: {len(real)}")
    print(f"Selected real: {len(selected_real)}")
    print(f"Mixed total: {len(mixed)}")
    print(f"Source counts: {dict(source_counts)}")
    print(f"Output path: {args.output_path}")
    print("Qwen v5 synthetic-real mix completed.")


if __name__ == "__main__":
    main()
