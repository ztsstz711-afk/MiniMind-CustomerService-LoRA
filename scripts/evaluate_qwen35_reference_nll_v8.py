"""Compare Qwen3.5 base and a LoRA adapter on held-out reference NLL.

This is a task-aligned SFT diagnostic: the supplied assistant reply is the
target.  It does not claim production quality or general customer-service
preference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(row: dict) -> str:
    raw = f"{row['source_dialogue_group']}:{row['source_turn_index']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def bootstrap_interval(values: list[float], samples: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    estimates = sorted(mean(values[rng.randrange(len(values))] for _ in values) for _ in range(samples))
    return [estimates[int(0.025 * (samples - 1))], estimates[int(0.975 * (samples - 1))]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate held-out assistant reference NLL for base and LoRA.")
    parser.add_argument("--model_name_or_path", type=Path, default=ROOT / "models" / "qwen3_5_4b")
    parser.add_argument("--adapter_path", type=Path, default=ROOT / "outputs" / "qwen35_4b_qlora_dch2_v8_run3" / "best_adapter")
    parser.add_argument("--test_file", type=Path, default=ROOT / "outputs" / "qwen35_dch2_protocol_v8" / "frozen_external_cases.jsonl")
    parser.add_argument("--output_dir", type=Path, default=ROOT / "outputs" / "qwen35_dch2_reference_nll_v8")
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--bootstrap_samples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def build_example(tokenizer, messages: list[dict], max_seq_length: int) -> tuple[list[int], list[int]]:
    full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False, return_tensors=None)
    prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=False, return_tensors=None)
    full_ids = list(full.input_ids if hasattr(full, "input_ids") else full)
    prompt_ids = list(prompt.input_ids if hasattr(prompt, "input_ids") else prompt)
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Completed conversation does not share the registered prompt prefix")
    if len(full_ids) > max_seq_length:
        raise ValueError("Full conversation exceeds max_seq_length")
    labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids):]
    if not any(value != -100 for value in labels):
        raise ValueError("No assistant target tokens")
    return full_ids, labels


def load_model(model_path: Path, adapter_path: Path | None, torch):
    from transformers import AutoModelForImageTextToText, BitsAndBytesConfig

    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        str(model_path), quantization_config=quant, device_map={"": 0}, local_files_only=True,
    )
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path), is_trainable=False)
    model.eval()
    return model


def evaluate_condition(condition: str, model, examples: list[dict], torch) -> list[dict]:
    rows = []
    with torch.inference_mode():
        for index, example in enumerate(examples, start=1):
            input_ids = torch.tensor([example["input_ids"]], dtype=torch.long, device="cuda")
            labels = torch.tensor([example["labels"]], dtype=torch.long, device="cuda")
            attention_mask = torch.ones_like(input_ids)
            loss = float(model(input_ids=input_ids, attention_mask=attention_mask, labels=labels).loss.detach().float().cpu())
            rows.append({
                "case_id": example["case_id"],
                "condition_id": condition,
                "assistant_tokens": example["assistant_tokens"],
                "mean_token_nll": loss,
                "total_token_nll": loss * example["assistant_tokens"],
            })
            if index == 1 or index % 20 == 0:
                print(f"{condition} {index}/{len(examples)}", flush=True)
    return rows


def main() -> None:
    args = parse_args()
    for path in (args.model_name_or_path, args.adapter_path, args.test_file):
        if not path.exists():
            raise FileNotFoundError(path)
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation: {args.output_dir}")

    import torch
    from transformers import AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the registered 4-bit comparison")
    tokenizer = AutoTokenizer.from_pretrained(str(args.model_name_or_path), local_files_only=True)
    rows = read_jsonl(args.test_file)
    examples, dropped = [], []
    for row in rows:
        try:
            input_ids, labels = build_example(tokenizer, row["messages"], args.max_seq_length)
        except ValueError as error:
            if str(error) != "Full conversation exceeds max_seq_length":
                raise
            dropped.append(stable_id(row))
            continue
        examples.append({
            "case_id": stable_id(row),
            "input_ids": input_ids,
            "labels": labels,
            "assistant_tokens": sum(value != -100 for value in labels),
        })
    if not examples:
        raise ValueError("No usable held-out references")

    model = load_model(args.model_name_or_path, None, torch)
    base = evaluate_condition("B0", model, examples, torch)
    del model
    torch.cuda.empty_cache()
    model = load_model(args.model_name_or_path, args.adapter_path, torch)
    candidate = evaluate_condition("R-DCH2", model, examples, torch)
    del model
    torch.cuda.empty_cache()

    by_base = {row["case_id"]: row for row in base}
    by_candidate = {row["case_id"]: row for row in candidate}
    if set(by_base) != set(by_candidate):
        raise RuntimeError("Condition case mismatch")
    deltas = [by_candidate[key]["mean_token_nll"] - by_base[key]["mean_token_nll"] for key in sorted(by_base)]
    base_token_total = sum(row["total_token_nll"] for row in base)
    candidate_token_total = sum(row["total_token_nll"] for row in candidate)
    token_count = sum(row["assistant_tokens"] for row in base)
    base_nll = base_token_total / token_count
    candidate_nll = candidate_token_total / token_count
    report = {
        "protocol": "qwen35_dch2_v8_heldout_reference_nll",
        "model": str(args.model_name_or_path),
        "adapter": str(args.adapter_path),
        "test_file": str(args.test_file),
        "test_file_sha256": sha256_file(args.test_file),
        "input_rows": len(rows),
        "evaluated_rows": len(examples),
        "dropped_over_length": len(dropped),
        "assistant_tokens": token_count,
        "conditions": {
            "B0": {"token_weighted_mean_nll": base_nll, "perplexity": math.exp(base_nll)},
            "R-DCH2": {"token_weighted_mean_nll": candidate_nll, "perplexity": math.exp(candidate_nll)},
        },
        "candidate_minus_base": {
            "token_weighted_mean_nll": candidate_nll - base_nll,
            "paired_case_mean_nll_delta": mean(deltas),
            "paired_case_mean_nll_delta_95_bootstrap_ci": bootstrap_interval(deltas, args.bootstrap_samples, args.seed),
            "cases_improved": sum(value < 0 for value in deltas),
            "cases_worsened": sum(value > 0 for value in deltas),
            "cases_tied": sum(value == 0 for value in deltas),
        },
        "success_rule": "Positive only if candidate mean NLL is lower and the paired case-level bootstrap interval is entirely below zero.",
        "boundary": "Measures fit to held-out supplied replies, not human preference, business impact, production quality, or generalized customer-service ability.",
    }
    args.output_dir.mkdir(parents=True)
    write_jsonl(args.output_dir / "per_case_nll.jsonl", [*base, *candidate])
    (args.output_dir / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(args.output_dir), "conditions": report["conditions"], "candidate_minus_base": report["candidate_minus_base"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
