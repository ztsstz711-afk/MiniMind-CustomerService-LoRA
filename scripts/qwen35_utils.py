"""Small shared helpers for the public Qwen3.5 customer-service workflow."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def require_packages():
    """Load QLoRA dependencies only when a GPU task actually runs."""
    try:
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing QLoRA dependency. Install PyTorch, transformers, peft, accelerate and bitsandbytes."
        ) from exc
    return (
        torch,
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        DataLoader,
        Dataset,
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )


def load_rows(path: Path) -> list[dict]:
    """Read strictly formatted system/user/assistant SFT rows."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing SFT data: {path}")
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            roles = [message.get("role") for message in record.get("messages", [])]
            if roles != ["system", "user", "assistant"]:
                raise ValueError(f"{path} line {line_number} must contain system/user/assistant messages")
            rows.append(record)
    if not rows:
        raise ValueError(f"No records found in {path}")
    return rows


def collate_batch(batch: list[dict], pad_token_id: int, torch):
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids, attention_mask, labels = [], [], []
    for item in batch:
        padding = max_len - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [pad_token_id] * padding)
        attention_mask.append(item["attention_mask"] + [0] * padding)
        labels.append(item["labels"] + [-100] * padding)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
    }


def set_lr(optimizer, base_lr: float, step: int, total_steps: int, warmup_steps: int) -> float:
    if step <= warmup_steps and warmup_steps > 0:
        lr = base_lr * step / warmup_steps
    else:
        progress = (step - warmup_steps) / max(total_steps - warmup_steps, 1)
        lr = base_lr * 0.5 * (1.0 + math.cos(math.pi * min(progress, 1.0)))
    for group in optimizer.param_groups:
        group["lr"] = lr
    return lr


def allocate_strata(counts: Counter, sample_size: int) -> dict[str, int]:
    if sample_size > sum(counts.values()):
        raise ValueError("sample_size exceeds available test records")
    ideal = {key: sample_size * value / sum(counts.values()) for key, value in counts.items()}
    allocation = {key: int(value) for key, value in ideal.items()}
    remainder = sample_size - sum(allocation.values())
    for key in sorted(counts, key=lambda item: (ideal[item] - allocation[item], item), reverse=True)[:remainder]:
        allocation[key] += 1
    return allocation


def stable_case_id(row: dict) -> str:
    value = f"{row['source_dialogue_group']}:{row['source_turn_index']}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()[:16]


def generate_rows(model, tokenizer, rows: list[dict], max_new_tokens: int, torch) -> dict[str, str]:
    """Greedily generate one answer per source-dialogue case."""
    model.eval()
    results: dict[str, str] = {}
    with torch.inference_mode():
        for index, row in enumerate(rows, start=1):
            encoded = tokenizer.apply_chat_template(
                row["messages"][:-1], tokenize=True, add_generation_prompt=True, return_tensors="pt"
            )
            input_ids = encoded.input_ids if hasattr(encoded, "input_ids") else encoded
            if input_ids.ndim == 1:
                input_ids = input_ids.unsqueeze(0)
            input_ids = input_ids.to("cuda:0")
            generated = model.generate(
                input_ids=input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
            results[stable_case_id(row)] = tokenizer.decode(
                generated[0, input_ids.shape[1] :], skip_special_tokens=True
            ).strip()
            if index % 10 == 0 or index == len(rows):
                print(f"generated {index}/{len(rows)}", flush=True)
    return results
