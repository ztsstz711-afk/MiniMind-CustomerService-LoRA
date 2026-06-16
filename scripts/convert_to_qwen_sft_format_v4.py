"""Convert v2 customer-service data into Qwen/TRL SFT messages format."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAIN_INPUT = PROJECT_ROOT / "data" / "train_v2.jsonl"
EVAL_INPUT = PROJECT_ROOT / "data" / "eval_v2.jsonl"
TRAIN_OUTPUT = PROJECT_ROOT / "data" / "qwen_train_v4.jsonl"
EVAL_OUTPUT = PROJECT_ROOT / "data" / "qwen_eval_v4.jsonl"

SYSTEM_PROMPT = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。"
    "你需要根据用户问题给出清晰、合规、不过度承诺的回复。"
    "遇到违规、不合理或无法确认的信息请求时，应礼貌拒绝，并给出合规替代方案。"
)
REQUIRED_FIELDS = {"instruction", "input", "output", "category", "difficulty", "tags"}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing input file: {path}")
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {path} at line {line_number}")
            record = json.loads(line)
            missing = REQUIRED_FIELDS - set(record)
            if missing:
                raise ValueError(f"{path} line {line_number} missing fields: {sorted(missing)}")
            if not str(record["input"]).strip() or not str(record["output"]).strip():
                raise ValueError(f"{path} line {line_number} has empty input/output")
            if not isinstance(record["tags"], list):
                raise TypeError(f"{path} line {line_number} tags must be list")
            rows.append(record)
    return rows


def convert_record(record: dict) -> dict:
    user_content = (
        f"场景：{record['category']}\n"
        f"难度：{record['difficulty']}\n"
        f"用户问题：{record['input']}\n"
        "请生成一段客服回复。"
    )
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": record["output"]},
        ],
        "category": record["category"],
        "difficulty": record["difficulty"],
        "tags": record["tags"],
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def convert_file(input_path: Path, output_path: Path) -> int:
    rows = [convert_record(record) for record in read_jsonl(input_path)]
    write_jsonl(output_path, rows)
    print(f"Converted {len(rows)} samples: {input_path} -> {output_path}")
    return len(rows)


def main() -> None:
    train_count = convert_file(TRAIN_INPUT, TRAIN_OUTPUT)
    eval_count = convert_file(EVAL_INPUT, EVAL_OUTPUT)
    print(f"Qwen train v4 samples: {train_count}")
    print(f"Qwen eval v4 samples: {eval_count}")


if __name__ == "__main__":
    main()
