"""Validate converted JSONL data against MiniMind SFTDataset expectations."""

import json
import random
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = {
    "train": PROJECT_ROOT / "data" / "minimind_train.jsonl",
    "eval": PROJECT_ROOT / "data" / "minimind_eval.jsonl",
}
ALLOWED_ROLES = {"system", "user", "assistant"}
REQUIRED_ROLES = {"user", "assistant"}
PREVIEW_COUNT = 2
RANDOM_SEED = 42


def fail(path: Path, line_number: int, message: str) -> None:
    """Raise a validation error with file and line context."""
    raise ValueError(f"{path}, line {line_number}: {message}")


def validate_message(path: Path, line_number: int, index: int, message: object) -> None:
    if not isinstance(message, dict):
        fail(path, line_number, f"message {index} must be a JSON object")

    missing = [field for field in ("role", "content") if field not in message]
    if missing:
        fail(
            path,
            line_number,
            f"message {index} is missing field(s): {', '.join(missing)}",
        )

    role = message["role"]
    content = message["content"]
    if role not in ALLOWED_ROLES:
        fail(
            path,
            line_number,
            f"message {index} has unsupported role {role!r}; "
            f"allowed roles: {sorted(ALLOWED_ROLES)}",
        )
    if not isinstance(content, str):
        fail(path, line_number, f"message {index} content must be a string")
    if role == "assistant" and not content.strip():
        fail(path, line_number, f"message {index} assistant content must not be empty")


def load_and_validate(path: Path) -> tuple[list[dict], Counter]:
    """Read one JSONL file and validate its MiniMind conversation structure."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    records = []
    role_counts: Counter = Counter()

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                fail(path, line_number, "blank lines are not allowed")

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(path, line_number, f"invalid JSON: {exc}")

            if not isinstance(record, dict):
                fail(path, line_number, "top-level value must be a JSON object")
            if "conversations" not in record:
                fail(path, line_number, "missing top-level field 'conversations'")

            conversations = record["conversations"]
            if not isinstance(conversations, list):
                fail(path, line_number, "'conversations' must be a list")
            if not conversations:
                fail(path, line_number, "'conversations' must not be empty")

            sample_roles = set()
            for index, message in enumerate(conversations):
                validate_message(path, line_number, index, message)
                role = message["role"]
                sample_roles.add(role)
                role_counts[role] += 1

            missing_roles = REQUIRED_ROLES - sample_roles
            if missing_roles:
                fail(
                    path,
                    line_number,
                    f"sample is missing required role(s): {', '.join(sorted(missing_roles))}",
                )

            records.append(record)

    if not records:
        raise ValueError(f"Data file contains no samples: {path}")
    return records, role_counts


def print_previews(records_by_split: dict[str, list[dict]]) -> None:
    """Print deterministic random previews from all validated records."""
    candidates = [
        (split, index, record)
        for split, records in records_by_split.items()
        for index, record in enumerate(records, start=1)
    ]
    random.seed(RANDOM_SEED)
    previews = random.sample(candidates, k=min(PREVIEW_COUNT, len(candidates)))

    print(f"Random sample previews (seed={RANDOM_SEED}):")
    for preview_number, (split, index, record) in enumerate(previews, start=1):
        rendered = json.dumps(record, ensure_ascii=False)
        print(f"Preview {preview_number} [{split} line {index}]: {rendered}")


def main() -> None:
    records_by_split = {}
    role_counts_by_split = {}

    for split, path in DATA_FILES.items():
        records, role_counts = load_and_validate(path)
        records_by_split[split] = records
        role_counts_by_split[split] = role_counts
        print(f"{split} file: {path}")
        print(f"{split} samples: {len(records)}")
        print(f"{split} role distribution: {dict(sorted(role_counts.items()))}")

    print_previews(records_by_split)
    print("MiniMind data smoke test passed.")


if __name__ == "__main__":
    main()
