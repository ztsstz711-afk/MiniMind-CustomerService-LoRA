"""Convert JDDC-like real customer-service data to Qwen SFT messages format.

This is an extensible draft. JDDC/JDDC 2.1 releases may use different field
names, so adapt `extract_turns` after inspecting the actual file with
scripts/inspect_real_data_v5.py.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。"
    "你需要根据用户问题给出清晰、合规、不过度承诺的回复。"
    "遇到违规、不合理或无法确认的信息请求时，应礼貌拒绝，并给出合规替代方案。"
)

PHONE_RE = re.compile(r"(?<!\d)(?:1[3-9]\d{9})(?!\d)")
ORDER_RE = re.compile(r"(?i)(订单号[:：]?\s*)?[A-Z0-9]{10,32}")
LONG_DIGIT_RE = re.compile(r"(?<!\d)\d{8,}(?!\d)")
GARBLED_RE = re.compile(r"[\ufffd]{1,}|[^\S\r\n]{8,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert JDDC-like data to Qwen SFT JSONL.")
    parser.add_argument("--input_path", type=Path, required=True)
    parser.add_argument("--output_path", type=Path, default=Path("data/qwen_real_train_v5.jsonl"))
    parser.add_argument("--max_samples", type=int, default=3000)
    return parser.parse_args()


def read_records(path: Path) -> list[Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing input file: {path}")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("data", "sessions", "dialogues", "conversations", "items"):
                if isinstance(data.get(key), list):
                    return data[key]
            return [data]
    raise ValueError(f"Unsupported input format: {path.suffix}")


def clean_text(text: Any) -> str:
    value = str(text or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = PHONE_RE.sub("[手机号]", value)
    value = ORDER_RE.sub(lambda match: "[订单号]" if any(ch.isdigit() for ch in match.group(0)) else match.group(0), value)
    value = LONG_DIGIT_RE.sub("[数字编号]", value)
    value = re.sub(r"(收货地址|地址)[:：]?\s*[^，。；;\n]{6,60}", r"\1：[地址已脱敏]", value)
    return value.strip()


def looks_bad(text: str) -> bool:
    if not text:
        return True
    if len(text) < 4:
        return True
    if GARBLED_RE.search(text):
        return True
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return len(text) >= 12 and chinese_chars == 0


def normalize_role(raw_role: Any) -> str | None:
    role = str(raw_role or "").lower()
    if role in {"user", "customer", "buyer", "client", "客户", "用户", "买家"}:
        return "user"
    if role in {"assistant", "service", "seller", "agent", "客服", "商家", "卖家"}:
        return "assistant"
    return None


def extract_turns(record: Any) -> list[dict]:
    """Extract normalized turns from one raw JDDC-like record.

    TODO: After downloading JDDC/JDDC 2.1, inspect real fields and adapt this
    function for the exact dialogue/session schema.
    """
    if isinstance(record, list):
        raw_turns = record
    elif isinstance(record, dict):
        for key in ("messages", "conversations", "dialogue", "dialog", "turns", "session", "chat"):
            if isinstance(record.get(key), list):
                raw_turns = record[key]
                break
        else:
            user_text = record.get("user") or record.get("question") or record.get("query") or record.get("input")
            assistant_text = record.get("assistant") or record.get("answer") or record.get("response") or record.get("reply")
            if user_text and assistant_text:
                raw_turns = [
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_text},
                ]
            else:
                return []
    else:
        return []

    turns = []
    for item in raw_turns:
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            continue
        role = normalize_role(item.get("role") or item.get("speaker") or item.get("sender") or item.get("from"))
        content = item.get("content") or item.get("text") or item.get("utterance") or item.get("message")
        content = clean_text(content)
        if role and not looks_bad(content):
            turns.append({"role": role, "content": content})
    return turns


def pair_turns(turns: list[dict]) -> list[tuple[str, str]]:
    pairs = []
    last_user = None
    for turn in turns:
        if turn["role"] == "user":
            last_user = turn["content"]
        elif turn["role"] == "assistant" and last_user:
            assistant = turn["content"]
            if not looks_bad(last_user) and not looks_bad(assistant):
                pairs.append((last_user, assistant))
            last_user = None
    return pairs


def main() -> None:
    args = parse_args()
    records = read_records(args.input_path)
    output_rows = []
    seen = set()
    for record in records:
        turns = extract_turns(record)
        for user_text, assistant_text in pair_turns(turns):
            key = (user_text, assistant_text)
            if key in seen:
                continue
            seen.add(key)
            output_rows.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_text},
                ],
                "source": "jddc",
                "category": "real_customer_service",
                "difficulty": "medium",
                "tags": ["real_data", "customer_service"],
            })
            if args.max_samples and len(output_rows) >= args.max_samples:
                break
        if args.max_samples and len(output_rows) >= args.max_samples:
            break

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    with args.output_path.open("w", encoding="utf-8") as file:
        for row in output_rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Input records: {len(records)}")
    print(f"Converted samples: {len(output_rows)}")
    print(f"Output path: {args.output_path}")
    print("JDDC to Qwen SFT v5 conversion completed.")


if __name__ == "__main__":
    main()
