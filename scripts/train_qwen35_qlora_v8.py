"""Text-only, 4-bit QLoRA SFT for the Qwen3.5 multimodal checkpoint.

The model is loaded through its official image-text auto class, while this
experiment supplies text conversation tokens only.  Loss is limited to the
assistant reply exactly as in the earlier controlled Qwen track.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from qwen35_utils import collate_batch, load_rows, set_lr


ROOT = Path(__file__).resolve().parents[1]
QUESTION_TAIL = re.compile(r"(?:吗|呢|么|嘛|否|多少|哪个|什么|如何|怎么)[？?]?$|[？?]$")


def parse_args() -> argparse.Namespace:
    protocol = ROOT / "outputs" / "qwen35_dch2_protocol_v8"
    parser = argparse.ArgumentParser(description="Train Qwen3.5-4B with controlled 4-bit QLoRA.")
    parser.add_argument("--model_name_or_path", type=Path, default=ROOT / "models" / "qwen3_5_4b")
    parser.add_argument("--train_file", type=Path, default=protocol / "train.jsonl")
    parser.add_argument("--dev_file", type=Path, default=protocol / "dev.jsonl")
    parser.add_argument("--output_dir", type=Path, default=ROOT / "outputs" / "qwen35_4b_qlora_dch2_v8_run2")
    parser.add_argument("--num_train_epochs", type=int, default=3)
    parser.add_argument("--per_device_train_batch_size", type=int, default=1)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=1)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--logging_steps", type=int, default=20)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--loss_normalization",
        choices=("example", "assistant_token"),
        default="assistant_token",
        help="Normalization for accumulated assistant-token loss; the final configuration uses 'assistant_token'.",
    )
    parser.add_argument(
        "--short_question_loss_weight",
        type=float,
        default=1.0,
        help="Train-only weight for assistant targets at or below --short_question_max_chars that end as questions.",
    )
    parser.add_argument(
        "--short_question_max_chars",
        type=int,
        default=30,
        help="Whitespace-normalized character threshold used by --short_question_loss_weight.",
    )
    return parser.parse_args()


def supervised_tokens(batch, torch) -> int:
    return int(torch.count_nonzero(batch["labels"] != -100).item())


def normalize_target_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text))


def is_short_question_target(messages: list[dict], max_chars: int) -> bool:
    target = normalize_target_text(messages[-1]["content"])
    return len(target) <= max_chars and bool(QUESTION_TAIL.search(target))


def accumulation_scale(
    target_tokens: int,
    example_weight: float,
    window_weighted_tokens: float,
    window_weight_total: float,
    loss_normalization: str,
) -> float:
    if loss_normalization == "assistant_token":
        return target_tokens * example_weight / window_weighted_tokens
    return example_weight / window_weight_total


def evaluate(model, loader, torch, loss_normalization: str) -> float:
    model.eval()
    total, weight_total = 0.0, 0
    with torch.inference_mode():
        for batch in loader:
            model_batch = {key: value.cuda() for key, value in batch.items() if key != "loss_weight"}
            loss = float(model(**model_batch).loss.detach().float().cpu())
            weight = supervised_tokens(model_batch, torch) if loss_normalization == "assistant_token" else model_batch["input_ids"].shape[0]
            total += loss * weight
            weight_total += weight
    model.train()
    return total / weight_total


def build_qwen35_assistant_only_example(tokenizer, messages: list[dict], max_seq_length: int) -> dict:
    """Mask the dialogue prefix without assuming Qwen3's generation suffix.

    Qwen3.5 adds a ``<think>`` scaffold differently for generation and for a
    completed assistant turn.  The stable boundary is therefore the completed
    system/user conversation, not ``add_generation_prompt=True``.
    """
    full = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False, return_tensors=None)
    prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=False, return_tensors=None)
    full_ids = list(full.input_ids if hasattr(full, "input_ids") else full)
    prompt_ids = list(prompt.input_ids if hasattr(prompt, "input_ids") else prompt)
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Qwen3.5 completed prompt is not a prefix of the full chat template")
    if len(full_ids) > max_seq_length:
        raise ValueError("Full conversation exceeds the registered sequence limit")
    input_ids = full_ids
    labels = [-100] * len(prompt_ids) + input_ids[len(prompt_ids):]
    if not any(token != -100 for token in labels):
        raise ValueError("Assistant reply was fully truncated")
    return {"input_ids": input_ids, "attention_mask": [1] * len(input_ids), "labels": labels}


def main() -> None:
    args = parse_args()
    if not 0.0 < args.short_question_loss_weight <= 1.0:
        raise ValueError("short_question_loss_weight must be in (0, 1]")
    if args.short_question_max_chars < 1:
        raise ValueError("short_question_max_chars must be positive")
    if args.short_question_loss_weight != 1.0 and args.per_device_train_batch_size != 1:
        raise ValueError("short-question weighting currently requires per_device_train_batch_size=1")
    for path in (args.model_name_or_path, args.train_file, args.dev_file):
        if not path.exists():
            raise FileNotFoundError(f"Required path missing: {path}")
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite a run: {args.output_dir}")
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from torch.utils.data import DataLoader, Dataset
    from transformers import AutoModelForImageTextToText, AutoTokenizer, BitsAndBytesConfig
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for QLoRA")
    random.seed(args.seed); torch.manual_seed(args.seed); torch.cuda.manual_seed_all(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(str(args.model_name_or_path), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=compute_dtype)
    model = AutoModelForImageTextToText.from_pretrained(str(args.model_name_or_path), quantization_config=quant, device_map={"": 0}, local_files_only=True)
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    train_rows, dev_rows = load_rows(args.train_file), load_rows(args.dev_file)

    class DatasetRows(Dataset):
        def __init__(self, rows, apply_short_question_weight: bool):
            self.examples, self.dropped_over_limit, self.short_question_rows = [], 0, 0
            self.short_question_supervised_tokens = 0
            self.total_supervised_tokens = 0
            for row in rows:
                try:
                    example = build_qwen35_assistant_only_example(tokenizer, row["messages"], args.max_seq_length)
                except ValueError as error:
                    if str(error) != "Full conversation exceeds the registered sequence limit":
                        raise
                    self.dropped_over_limit += 1
                    continue
                is_short_question = is_short_question_target(row["messages"], args.short_question_max_chars)
                target_tokens = sum(token != -100 for token in example["labels"])
                example["loss_weight"] = (
                    args.short_question_loss_weight
                    if apply_short_question_weight and is_short_question
                    else 1.0
                )
                example["is_short_question"] = is_short_question
                self.examples.append(example)
                self.total_supervised_tokens += target_tokens
                if is_short_question:
                    self.short_question_rows += 1
                    self.short_question_supervised_tokens += target_tokens
            if not self.examples:
                raise ValueError("No usable examples remain after the registered sequence-limit filter")
        def __len__(self): return len(self.examples)
        def __getitem__(self, index): return self.examples[index]

    train_set = DatasetRows(train_rows, apply_short_question_weight=True)
    dev_set = DatasetRows(dev_rows, apply_short_question_weight=False)

    def collate(rows):
        batch = collate_batch(rows, tokenizer.pad_token_id, torch)
        batch["loss_weight"] = torch.tensor([row["loss_weight"] for row in rows], dtype=torch.float32)
        return batch
    train_loader = DataLoader(train_set, batch_size=args.per_device_train_batch_size, shuffle=True, collate_fn=collate)
    dev_loader = DataLoader(dev_set, batch_size=args.per_device_eval_batch_size, shuffle=False, collate_fn=collate)
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=args.learning_rate)
    forwards = len(train_loader) * args.num_train_epochs
    total_steps = math.ceil(forwards / args.gradient_accumulation_steps)
    warmup_steps = int(total_steps * args.warmup_ratio)
    args.output_dir.mkdir(parents=True)
    meta = {"protocol": "qwen35_dch2_v8_qlora", "started_at_utc": datetime.now(timezone.utc).isoformat(), "python": sys.executable, "model": str(args.model_name_or_path), "train_file": str(args.train_file), "dev_file": str(args.dev_file), "arguments": vars(args), "assistant_only_loss": True, "loss_normalization": args.loss_normalization, "short_question_weighting": {"enabled": args.short_question_loss_weight != 1.0, "max_chars": args.short_question_max_chars, "loss_weight": args.short_question_loss_weight, "train_rows": train_set.short_question_rows, "train_row_share": train_set.short_question_rows / len(train_set), "train_supervised_tokens": train_set.short_question_supervised_tokens, "train_supervised_token_share": train_set.short_question_supervised_tokens / train_set.total_supervised_tokens, "dev_loss_is_unweighted": True}, "quantization": "4-bit NF4 double quant", "train_records_input": len(train_rows), "dev_records_input": len(dev_rows), "train_records": len(train_set), "dev_records": len(dev_set), "dropped_full_conversations_over_sequence_limit": {"train": train_set.dropped_over_limit, "dev": dev_set.dropped_over_limit}, "boundary": "Development loss measures unweighted fit to held-out local DCH-2 replies, not output quality."}
    meta["arguments"] = {key: str(value) if isinstance(value, Path) else value for key, value in meta["arguments"].items()}
    (args.output_dir / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    best, history, forward, step = float("inf"), [], 0, 0
    optimizer.zero_grad(set_to_none=True)
    for epoch in range(1, args.num_train_epochs + 1):
        started, total_loss, weighted_loss, objective_loss = time.monotonic(), 0.0, 0.0, 0.0
        rows_seen, tokens_seen, objective_weight_seen = 0, 0, 0.0
        loader_iterator = iter(train_loader)
        while True:
            window = []
            for _ in range(args.gradient_accumulation_steps):
                try:
                    window.append(next(loader_iterator))
                except StopIteration:
                    break
            if not window:
                break
            window_tokens = [supervised_tokens(batch, torch) for batch in window]
            window_weights = [float(batch["loss_weight"].mean().item()) for batch in window]
            window_weighted_tokens = sum(tokens * weight for tokens, weight in zip(window_tokens, window_weights))
            window_weight_total = sum(window_weights)
            for batch in window:
                forward += 1
                example_weight = float(batch["loss_weight"].mean().item())
                model_batch = {key: value.cuda() for key, value in batch.items() if key != "loss_weight"}
                target_tokens = supervised_tokens(model_batch, torch)
                loss = model(**model_batch).loss
                scale = accumulation_scale(
                    target_tokens,
                    example_weight,
                    window_weighted_tokens,
                    window_weight_total,
                    args.loss_normalization,
                )
                (loss * scale).backward()
                detached_loss = float(loss.detach().float().cpu())
                batch_rows = batch["input_ids"].shape[0]
                total_loss += detached_loss * batch_rows
                weighted_loss += detached_loss * target_tokens
                objective_loss += detached_loss * target_tokens * example_weight
                rows_seen += batch_rows
                tokens_seen += target_tokens
                objective_weight_seen += target_tokens * example_weight
                if forward == 1 or forward % args.logging_steps == 0:
                    print(f"step={forward}/{forwards} epoch={epoch} loss={detached_loss:.6f} lr={optimizer.param_groups[0]['lr']:.8f}", flush=True)
            step += 1
            lr = set_lr(optimizer, args.learning_rate, step, total_steps, warmup_steps)
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        dev_loss = evaluate(model, dev_loader, torch, args.loss_normalization)
        metric = {"epoch": epoch, "train_loss": total_loss / rows_seen, "train_token_weighted_loss": weighted_loss / tokens_seen, "train_objective_weighted_loss": objective_loss / objective_weight_seen, "dev_loss": dev_loss, "dev_loss_normalization": args.loss_normalization, "dev_loss_short_question_weight": 1.0, "optimizer_step": step, "epoch_seconds": round(time.monotonic() - started, 2)}; history.append(metric); print(json.dumps(metric), flush=True)
        if dev_loss < best:
            best = dev_loss; model.save_pretrained(str(args.output_dir / "best_adapter"), safe_serialization=True); tokenizer.save_pretrained(str(args.output_dir / "best_adapter"))
    model.save_pretrained(str(args.output_dir / "last_adapter"), safe_serialization=True); tokenizer.save_pretrained(str(args.output_dir / "last_adapter"))
    (args.output_dir / "metrics.json").write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_dev_loss": best, "output_dir": str(args.output_dir)}), flush=True)


if __name__ == "__main__":
    main()
