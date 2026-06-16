"""Train Qwen2.5-1.5B LoRA v4 on the full 800-sample dataset.

This script uses a conservative manual PyTorch + PEFT training loop to avoid
version-specific Trainer behavior. It saves only the LoRA adapter.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "qwen2_5_1_5b_instruct"
DEFAULT_TRAIN_FILE = PROJECT_ROOT / "data" / "qwen_train_v4.jsonl"
DEFAULT_EVAL_FILE = PROJECT_ROOT / "data" / "qwen_eval_v4.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "qwen2_5_1_5b_lora_v4"


class MessageDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_seq_length: int):
        self.rows = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    self.rows.append(json.loads(line))
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict:
        record = self.rows[index]
        text = self.tokenizer.apply_chat_template(
            record["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        encoded = self.tokenizer(
            text,
            max_length=self.max_seq_length,
            truncation=True,
            add_special_tokens=False,
        )
        input_ids = torch.tensor(encoded["input_ids"], dtype=torch.long)
        attention_mask = torch.tensor(encoded["attention_mask"], dtype=torch.long)
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone(),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Qwen2.5 LoRA v4.")
    parser.add_argument("--model_name_or_path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--train_file", type=Path, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--eval_file", type=Path, default=DEFAULT_EVAL_FILE)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--num_train_epochs", type=int, default=2)
    parser.add_argument("--per_device_train_batch_size", type=int, default=1)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--logging_steps", type=int, default=5)
    parser.add_argument("--warmup_ratio", type=float, default=0.03)
    parser.add_argument("--weight_decay", type=float, default=0.0)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    return parser.parse_args()


def print_cuda_memory(prefix: str) -> None:
    if not torch.cuda.is_available():
        print(f"{prefix} CUDA memory: no cuda")
        return
    allocated = torch.cuda.memory_allocated() / (1024**3)
    reserved = torch.cuda.memory_reserved() / (1024**3)
    print(f"{prefix} CUDA memory allocated: {allocated:.3f} GB")
    print(f"{prefix} CUDA memory reserved: {reserved:.3f} GB")


def collate_batch(batch: list[dict], pad_token_id: int) -> dict:
    max_len = max(item["input_ids"].numel() for item in batch)
    input_ids = []
    attention_mask = []
    labels = []
    for item in batch:
        pad_len = max_len - item["input_ids"].numel()
        input_ids.append(torch.cat([
            item["input_ids"],
            torch.full((pad_len,), pad_token_id, dtype=torch.long),
        ]))
        attention_mask.append(torch.cat([
            item["attention_mask"],
            torch.zeros(pad_len, dtype=torch.long),
        ]))
        labels.append(torch.cat([
            item["labels"],
            torch.full((pad_len,), -100, dtype=torch.long),
        ]))
    return {
        "input_ids": torch.stack(input_ids),
        "attention_mask": torch.stack(attention_mask),
        "labels": torch.stack(labels),
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


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Qwen LoRA v4 training.")
    if not args.model_name_or_path.is_dir():
        raise FileNotFoundError(f"Missing local Qwen model: {args.model_name_or_path}")
    if not args.train_file.is_file():
        raise FileNotFoundError(f"Missing train file: {args.train_file}")
    if args.eval_file and not args.eval_file.is_file():
        raise FileNotFoundError(f"Missing eval file: {args.eval_file}")

    print(f"Python executable: {sys.executable}")
    print(f"torch version: {torch.__version__}")
    print(f"Model path: {args.model_name_or_path}")
    print(f"Train file: {args.train_file}")
    print(f"Eval file: {args.eval_file}")
    print(f"Output dir: {args.output_dir}")
    print(f"epochs: {args.num_train_epochs}")
    print(f"batch_size: {args.per_device_train_batch_size}")
    print(f"gradient_accumulation_steps: {args.gradient_accumulation_steps}")
    print(f"learning_rate: {args.learning_rate}")
    print(f"max_seq_length: {args.max_seq_length}")
    print_cuda_memory("Before load")

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model_name_or_path),
        trust_remote_code=True,
        local_files_only=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(args.model_name_or_path),
        torch_dtype=torch.bfloat16,
        device_map={"": "cuda:0"},
        trust_remote_code=True,
        local_files_only=True,
    )
    model.config.use_cache = False
    print_cuda_memory("After load")

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    model.train()

    dataset = MessageDataset(args.train_file, tokenizer, args.max_seq_length)
    loader = DataLoader(
        dataset,
        batch_size=args.per_device_train_batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate_batch(batch, tokenizer.pad_token_id),
    )
    print(f"Train samples: {len(dataset)}")
    print(f"Train batches per epoch: {len(loader)}")

    trainable_params = [param for param in model.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    total_forward_steps = len(loader) * args.num_train_epochs
    total_optimizer_steps = math.ceil(total_forward_steps / args.gradient_accumulation_steps)
    warmup_steps = int(total_optimizer_steps * args.warmup_ratio)
    print(f"Total forward steps: {total_forward_steps}")
    print(f"Total optimizer steps: {total_optimizer_steps}")
    print(f"Warmup optimizer steps: {warmup_steps}")

    optimizer.zero_grad(set_to_none=True)
    global_step = 0
    optimizer_step = 0
    last_loss = None
    for epoch in range(args.num_train_epochs):
        for batch in loader:
            global_step += 1
            batch = {key: value.to("cuda:0") for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / args.gradient_accumulation_steps
            loss.backward()
            last_loss = float(loss.detach().cpu()) * args.gradient_accumulation_steps

            should_step = (
                global_step % args.gradient_accumulation_steps == 0
                or global_step == total_forward_steps
            )
            if should_step:
                optimizer_step += 1
                lr = set_lr(
                    optimizer,
                    args.learning_rate,
                    optimizer_step,
                    total_optimizer_steps,
                    warmup_steps,
                )
                torch.nn.utils.clip_grad_norm_(trainable_params, args.max_grad_norm)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            else:
                lr = optimizer.param_groups[0]["lr"]

            if global_step % args.logging_steps == 0 or global_step == 1 or global_step == total_forward_steps:
                print(
                    f"loss step={global_step} epoch={epoch + 1}/{args.num_train_epochs} "
                    f"optimizer_step={optimizer_step}/{total_optimizer_steps} "
                    f"loss={last_loss:.6f} lr={lr:.8f}"
                )

            del batch, outputs, loss

    if last_loss is None:
        raise RuntimeError("No loss was produced during Qwen LoRA v4 training.")
    if not math.isfinite(last_loss):
        raise RuntimeError(f"Non-finite loss detected: {last_loss}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.output_dir), safe_serialization=True)
    print_cuda_memory("After train")
    print(f"last_loss={last_loss:.6f}")
    print(f"adapter output path: {args.output_dir}")
    print("Qwen LoRA v4 training completed.")


if __name__ == "__main__":
    main()
