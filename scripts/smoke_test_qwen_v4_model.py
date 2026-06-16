"""Smoke test Qwen2.5 model loading and generation for v4.

This script only downloads/loads the base model and runs one short generation.
It does not train, does not apply LoRA, and does not modify MiniMind source code.
"""

import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_PROMPT = "用户说：我的订单三天没更新物流了，你作为电商售后客服应该怎么回复？"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen v4 model smoke test.")
    parser.add_argument("--model_name_or_path", default=DEFAULT_MODEL)
    parser.add_argument("--max_new_tokens", type=int, default=160)
    return parser.parse_args()


def print_cuda_memory(prefix: str) -> None:
    if not torch.cuda.is_available():
        print(f"{prefix} CUDA memory: no cuda")
        return
    allocated = torch.cuda.memory_allocated() / (1024**3)
    reserved = torch.cuda.memory_reserved() / (1024**3)
    print(f"{prefix} CUDA memory allocated: {allocated:.3f} GB")
    print(f"{prefix} CUDA memory reserved: {reserved:.3f} GB")


def load_model_with_fallback(model_name_or_path: str):
    last_error = None
    local_path = Path(model_name_or_path)
    is_local_path = local_path.exists()
    resolved_name_or_path = str(local_path.resolve()) if is_local_path else model_name_or_path
    print(f"local path: {is_local_path}")
    if is_local_path:
        print(f"resolved local path: {resolved_name_or_path}")
    for dtype in (torch.bfloat16, torch.float16):
        try:
            print(f"Trying torch_dtype: {dtype}")
            tokenizer = AutoTokenizer.from_pretrained(
                resolved_name_or_path,
                trust_remote_code=True,
                use_fast=True,
                local_files_only=is_local_path,
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            print("tokenizer loaded: True")

            model = AutoModelForCausalLM.from_pretrained(
                resolved_name_or_path,
                torch_dtype=dtype,
                device_map="auto",
                trust_remote_code=True,
                local_files_only=is_local_path,
            )
            model.eval()
            print("model loaded: True")
            print(f"model dtype used: {dtype}")
            return tokenizer, model, dtype
        except Exception as exc:
            last_error = exc
            print(f"Load failed with {dtype}: {type(exc).__name__}: {exc}")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    raise RuntimeError(
        f"Failed to load model with bfloat16 or float16. Last error: {type(last_error).__name__}: {last_error}"
    ) from last_error


@torch.inference_mode()
def generate(tokenizer, model, prompt: str, max_new_tokens: int) -> str:
    messages = [
        {
            "role": "system",
            "content": "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。",
        },
        {"role": "user", "content": prompt},
    ]
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    generated = output_ids[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    print(f"Python executable: {sys.executable}")
    print(f"torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(
        "GPU name: "
        + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda")
    )
    print(f"model name: {args.model_name_or_path}")
    print_cuda_memory("Before load")

    tokenizer, model, _dtype = load_model_with_fallback(args.model_name_or_path)
    print_cuda_memory("After load")

    output = generate(tokenizer, model, DEFAULT_PROMPT, args.max_new_tokens)
    print("generated output:")
    print(output)
    print_cuda_memory("After generation")
    print("Qwen v4 model smoke test completed.")


if __name__ == "__main__":
    main()
