"""Convert v2 SFT data to MiniMind conversations format."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SYSTEM_PROMPT = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。"
    "你需要根据用户问题给出清晰、合规、不过度承诺的回复。"
    "遇到违规、不合理或无法确认的信息请求时，应礼貌拒绝，并给出合规替代方案。"
)
TASKS = (
    (DATA_DIR / "train_v2.jsonl", DATA_DIR / "minimind_train_v2.jsonl"),
    (DATA_DIR / "eval_v2.jsonl", DATA_DIR / "minimind_eval_v2.jsonl"),
)
REQUIRED_FIELDS = {"instruction", "input", "output", "category", "difficulty", "tags"}


def convert_record(record):
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    user_content = (
        f"场景：{record['category']}\n"
        f"难度：{record['difficulty']}\n"
        f"用户问题：{record['input']}\n"
        "请生成一段客服回复。"
    )
    return {
        "conversations": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": record["output"]},
        ]
    }


def convert_file(input_path, output_path):
    converted = []
    with input_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                converted.append(convert_record(json.loads(line)))
            except Exception as exc:
                raise ValueError(f"{input_path}, line {line_number}: {exc}") from exc

    with output_path.open("w", encoding="utf-8") as file:
        for record in converted:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Converted {len(converted)} samples: {input_path} -> {output_path}")


def main():
    for input_path, output_path in TASKS:
        convert_file(input_path, output_path)


if __name__ == "__main__":
    main()
