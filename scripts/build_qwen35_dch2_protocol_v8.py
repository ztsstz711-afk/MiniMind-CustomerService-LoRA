"""Create the local-only Qwen3.5/DCH-2 training protocol.

This does not alter the provider data.  It makes a deterministic, source-group
disjoint train/dev split from the provider train partition and a fixed external
evaluation sample from the separate provider partition.  The source agreement
keeps every emitted JSONL under ignored ``outputs/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stable_key(seed: str, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a group-safe local Qwen3.5 DCH-2 protocol.")
    parser.add_argument("--provider_train", type=Path, default=ROOT / "data" / "qwen_train_dch2_v7_local.jsonl")
    parser.add_argument("--provider_external_eval", type=Path, default=ROOT / "data" / "qwen_external_eval_dch2_v7_local.jsonl")
    parser.add_argument("--output_dir", type=Path, default=ROOT / "outputs" / "qwen35_dch2_protocol_v8")
    parser.add_argument("--dev_group_ratio", type=float, default=0.10)
    parser.add_argument("--frozen_cases", type=int, default=120)
    parser.add_argument("--seed", default="qwen35-dch2-v8-20260928")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0 < args.dev_group_ratio < 0.5:
        raise ValueError("dev_group_ratio must be between 0 and 0.5")
    provider_train, external = read_jsonl(args.provider_train), read_jsonl(args.provider_external_eval)
    if not provider_train or not external:
        raise ValueError("Both provider partitions must be non-empty")
    required = {"messages", "source_dialogue_group", "source_turn_index"}
    for label, rows in (("provider_train", provider_train), ("provider_external_eval", external)):
        for index, row in enumerate(rows, start=1):
            if required - row.keys() or [message.get("role") for message in row["messages"]] != ["system", "user", "assistant"]:
                raise ValueError(f"{label} row {index} violates the admitted DCH-2 schema")

    train_groups = sorted({str(row["source_dialogue_group"]) for row in provider_train})
    dev_count = max(1, round(len(train_groups) * args.dev_group_ratio))
    dev_groups = set(sorted(train_groups, key=lambda group: stable_key(args.seed, group))[:dev_count])
    train_rows = [row for row in provider_train if str(row["source_dialogue_group"]) not in dev_groups]
    dev_rows = [row for row in provider_train if str(row["source_dialogue_group"]) in dev_groups]
    if not train_rows or not dev_rows:
        raise ValueError("Group split produced an empty partition")

    # The external provider partition has a few repeated prompts.  Keep one
    # deterministic turn per source dialogue and then sample source groups.
    one_per_group: dict[str, dict] = {}
    for row in sorted(external, key=lambda item: (str(item["source_dialogue_group"]), int(item["source_turn_index"]))):
        one_per_group.setdefault(str(row["source_dialogue_group"]), row)
    candidates = sorted(one_per_group.values(), key=lambda row: stable_key(args.seed, str(row["source_dialogue_group"])))
    if len(candidates) < args.frozen_cases:
        raise ValueError("Not enough external source groups for requested frozen cases")
    frozen_rows = sorted(candidates[:args.frozen_cases], key=lambda row: stable_key(args.seed, str(row["source_dialogue_group"])))

    train_groups_set = {str(row["source_dialogue_group"]) for row in train_rows}
    external_groups = {str(row["source_dialogue_group"]) for row in external}
    if train_groups_set & dev_groups or (train_groups_set | dev_groups) & external_groups:
        raise RuntimeError("Source-dialogue group leakage detected")

    args.output_dir.mkdir(parents=True, exist_ok=False)
    train_path, dev_path, frozen_path = (args.output_dir / name for name in ("train.jsonl", "dev.jsonl", "frozen_external_cases.jsonl"))
    write_jsonl(train_path, train_rows)
    write_jsonl(dev_path, dev_rows)
    write_jsonl(frozen_path, frozen_rows)
    manifest = {
        "protocol": "qwen35_dch2_v8_local_only",
        "source": {"provider_train": str(args.provider_train), "provider_external_eval": str(args.provider_external_eval)},
        "seed": args.seed,
        "splits": {
            "train": {"records": len(train_rows), "source_dialogue_groups": len(train_groups_set)},
            "dev": {"records": len(dev_rows), "source_dialogue_groups": len(dev_groups)},
            "frozen_external": {"records": len(frozen_rows), "source_dialogue_groups": len({str(row['source_dialogue_group']) for row in frozen_rows})},
        },
        "leakage_checks": {"train_dev_shared_groups": 0, "provider_train_external_shared_groups": 0},
        "boundary": "Local-only DCH-2 derivatives. Frozen external cases were never used for training or early stopping; they are not real traffic or a production benchmark.",
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(args.output_dir), "splits": manifest["splits"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
