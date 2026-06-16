"""Run a tiny Qwen2.5 PEFT LoRA smoke training.

This script trains on only 20 samples to validate the training path. It does not
run the full 800-sample Qwen LoRA experiment and saves only the LoRA adapter.
"""

import json
import math
import sys
import traceback
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "qwen2_5_1_5b_instruct"
TRAIN_PATH = PROJECT_ROOT / "data" / "qwen_train_smoke_v4.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "qwen_lora_smoke_v4"
STDOUT_LOG = OUTPUT_DIR / "train_stdout.txt"
STDERR_LOG = OUTPUT_DIR / "train_stderr.txt"

MAX_SEQ_LENGTH = 512
BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 1


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


class MessageDataset(Dataset):
    def __init__(self, path: Path, tokenizer):
        self.rows = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    self.rows.append(json.loads(line))
        self.tokenizer = tokenizer

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
            max_length=MAX_SEQ_LENGTH,
            truncation=True,
            add_special_tokens=False,
        )
        input_ids = encoded["input_ids"]
        attention_mask = encoded["attention_mask"]
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(input_ids, dtype=torch.long),
        }


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


def main_impl() -> None:
    if not MODEL_PATH.is_dir():
        raise FileNotFoundError(f"Missing local Qwen model: {MODEL_PATH}")
    if not TRAIN_PATH.is_file():
        raise FileNotFoundError(f"Missing smoke train data: {TRAIN_PATH}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this Qwen LoRA smoke test.")

    print(f"Python executable: {sys.executable}")
    print(f"torch version: {torch.__version__}")
    print(f"Model path: {MODEL_PATH}")
    print(f"Train path: {TRAIN_PATH}")
    print(f"Output dir: {OUTPUT_DIR}")
    print_cuda_memory("Before load")

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_PATH),
        trust_remote_code=True,
        local_files_only=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_PATH),
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

    dataset = MessageDataset(TRAIN_PATH, tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=lambda batch: collate_batch(batch, tokenizer.pad_token_id),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    total_steps = math.ceil(len(loader) / GRADIENT_ACCUMULATION_STEPS)
    print(f"Smoke samples: {len(dataset)}")
    print(f"Optimizer steps expected: {total_steps}")

    optimizer.zero_grad(set_to_none=True)
    global_step = 0
    optimizer_step = 0
    last_loss = None
    for epoch in range(NUM_EPOCHS):
        for batch in loader:
            global_step += 1
            batch = {key: value.to("cuda:0") for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / GRADIENT_ACCUMULATION_STEPS
            loss.backward()
            last_loss = float(loss.detach().cpu()) * GRADIENT_ACCUMULATION_STEPS
            print(f"loss step={global_step} epoch={epoch + 1}/{NUM_EPOCHS} loss={last_loss:.6f}")

            if global_step % GRADIENT_ACCUMULATION_STEPS == 0 or global_step == len(loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_step += 1
                print(f"optimizer_step={optimizer_step}")

    if last_loss is None:
        raise RuntimeError("No loss was produced during smoke training.")
    if not math.isfinite(last_loss):
        raise RuntimeError(f"Non-finite loss detected: {last_loss}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(OUTPUT_DIR), safe_serialization=True)
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print_cuda_memory("After train")
    print(f"last_loss={last_loss:.6f}")
    print(f"adapter output path: {OUTPUT_DIR}")
    print("Qwen LoRA smoke v4 training completed.")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with STDOUT_LOG.open("w", encoding="utf-8") as stdout_file, STDERR_LOG.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = Tee(original_stdout, stdout_file)
        sys.stderr = Tee(original_stderr, stderr_file)
        try:
            main_impl()
        except Exception:
            traceback.print_exc()
            raise
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    main()
