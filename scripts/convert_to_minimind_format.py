"""Convert customer-service SFT data to MiniMind conversation JSONL format."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SYSTEM_PROMPT = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。"
    "你需要根据用户问题给出清晰、合规、不过度承诺的回复。"
)
REQUIRED_FIELDS = ("instruction", "input", "output", "category")
CONVERSION_TASKS = (
    (DATA_DIR / "train.jsonl", DATA_DIR / "minimind_train.jsonl"),
    (DATA_DIR / "eval.jsonl", DATA_DIR / "minimind_eval.jsonl"),
)


def validate_record(record: object, input_path: Path, line_number: int) -> dict:
    """Validate one source record and return it with a narrowed dictionary type."""
    if not isinstance(record, dict):
        raise ValueError(
            f"Invalid record in {input_path} at line {line_number}: "
            "expected a JSON object."
        )

    missing_fields = [field for field in REQUIRED_FIELDS if field not in record]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(
            f"Missing required field(s) in {input_path} at line {line_number}: {missing}"
        )

    empty_fields = [
        field
        for field in REQUIRED_FIELDS
        if not isinstance(record[field], str) or not record[field].strip()
    ]
    if empty_fields:
        empty = ", ".join(empty_fields)
        raise ValueError(
            f"Required field(s) must be non-empty strings in {input_path} "
            f"at line {line_number}: {empty}"
        )

    return record


def convert_record(record: dict) -> dict:
    """Convert one instruction-style sample into a MiniMind conversation sample."""
    user_content = (
        f"场景：{record['category'].strip()}\n"
        f"用户问题：{record['input'].strip()}\n"
        "请生成一段客服回复。"
    )
    return {
        "conversations": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": record["output"].strip()},
        ]
    }


def convert_file(input_path: Path, output_path: Path) -> int:
    """Convert one JSONL file and return the number of written samples."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    converted_records = []
    with input_path.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {input_path} at line {line_number}: {exc}"
                ) from exc
            converted_records.append(
                convert_record(validate_record(record, input_path, line_number))
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in converted_records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")
    print(f"Converted samples: {len(converted_records)}")
    return len(converted_records)


def preview_output(output_path: Path, limit: int = 2) -> None:
    """Read and validate the first converted samples, then print them."""
    previews = []
    expected_roles = ["system", "user", "assistant"]

    with output_path.open("r", encoding="utf-8") as output_file:
        for line_number, line in enumerate(output_file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            conversations = record.get("conversations")
            if not isinstance(conversations, list) or len(conversations) != 3:
                raise ValueError(
                    f"Invalid conversations in {output_path} at line {line_number}: "
                    "expected exactly three messages."
                )

            roles = [message.get("role") for message in conversations]
            if roles != expected_roles:
                raise ValueError(
                    f"Invalid role order in {output_path} at line {line_number}: {roles}"
                )

            if any(
                not isinstance(message.get("content"), str)
                or not message["content"].strip()
                for message in conversations
            ):
                raise ValueError(
                    f"Empty message content in {output_path} at line {line_number}."
                )

            if len(previews) < limit:
                previews.append(record)

    print(f"First {len(previews)} samples from {output_path}:")
    for index, record in enumerate(previews, start=1):
        print(f"Sample {index}: {json.dumps(record, ensure_ascii=False)}")


def main() -> None:
    for input_path, output_path in CONVERSION_TASKS:
        convert_file(input_path, output_path)
        preview_output(output_path)


if __name__ == "__main__":
    main()
