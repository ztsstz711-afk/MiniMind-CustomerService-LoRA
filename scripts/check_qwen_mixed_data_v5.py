"""Check mixed Qwen v5 SFT data."""

import argparse
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROLES = ["system", "user", "assistant"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check mixed Qwen v5 data.")
    parser.add_argument("--data_path", type=Path, default=PROJECT_ROOT / "data" / "qwen_train_mixed_v5.jsonl")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.data_path)
    source_counts = Counter()
    tag_counts = Counter()
    empty_assistant = []
    bad_messages = []
    duplicate_pairs = Counter()

    for index, row in enumerate(rows, start=1):
        source_counts[row.get("source", "unknown")] += 1
        for tag in row.get("tags", []):
            tag_counts[tag] += 1
        messages = row.get("messages")
        if not isinstance(messages, list):
            bad_messages.append(index)
            continue
        roles = [message.get("role") for message in messages if isinstance(message, dict)]
        if roles[:3] != REQUIRED_ROLES:
            bad_messages.append(index)
            continue
        user = str(messages[1].get("content", "")).strip()
        assistant = str(messages[2].get("content", "")).strip()
        if not assistant:
            empty_assistant.append(index)
        duplicate_pairs[(user, assistant)] += 1

    duplicate_count = sum(count - 1 for count in duplicate_pairs.values() if count > 1)
    print(f"Data path: {args.data_path}")
    print(f"Total samples: {len(rows)}")
    print(f"Source distribution: {dict(source_counts)}")
    print(f"Tag distribution top 30: {dict(tag_counts.most_common(30))}")
    print(f"Bad messages rows: {len(bad_messages)}")
    print(f"Empty assistant rows: {len(empty_assistant)}")
    print(f"Duplicate user+assistant pairs: {duplicate_count}")
    if bad_messages:
        raise ValueError(f"Bad messages at rows: {bad_messages[:20]}")
    if empty_assistant:
        raise ValueError(f"Empty assistant at rows: {empty_assistant[:20]}")
    print("Qwen mixed data v5 check completed.")


if __name__ == "__main__":
    main()
