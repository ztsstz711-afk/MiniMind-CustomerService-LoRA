"""Run one deterministic reply with a local Qwen3.5 base and LoRA adapter."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_SYSTEM = "你是专业、礼貌的中文客服。仅根据用户提供的信息回复，不要虚构订单、政策或已执行操作。"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one reply with Qwen3.5-4B and a local LoRA adapter.")
    parser.add_argument("--model_name_or_path", type=Path, default=Path("models/qwen3_5_4b"))
    parser.add_argument(
        "--adapter_path",
        type=Path,
        default=Path("outputs/qwen35_4b_qlora_dch2_token_v10_run2/best_adapter"),
    )
    parser.add_argument("--prompt", required=True, help="Customer message or visible dialogue context.")
    parser.add_argument("--system", default=DEFAULT_SYSTEM)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.model_name_or_path.is_dir():
        raise FileNotFoundError(f"Model path does not exist: {args.model_name_or_path}")
    if not args.adapter_path.is_dir():
        raise FileNotFoundError(f"Adapter path does not exist: {args.adapter_path}")

    try:
        import torch
        from peft import PeftModel
        from transformers import (
            AutoConfig,
            AutoModelForCausalLM,
            AutoModelForImageTextToText,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
    except ImportError as exc:
        raise RuntimeError("Install the dependencies in requirements-qwen-qlora.txt first.") from exc

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for 4-bit QLoRA inference.")

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model_name_or_path), trust_remote_code=True, local_files_only=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )
    architecture = AutoConfig.from_pretrained(
        str(args.model_name_or_path), local_files_only=True
    ).model_type
    model_loader = AutoModelForImageTextToText if architecture == "qwen3_5" else AutoModelForCausalLM
    base_model = model_loader.from_pretrained(
        str(args.model_name_or_path),
        quantization_config=quantization_config,
        device_map={"": 0},
        trust_remote_code=True,
        local_files_only=True,
    )
    model = PeftModel.from_pretrained(base_model, str(args.adapter_path), local_files_only=True)
    model.eval()
    model.config.use_cache = True

    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": args.prompt},
    ]
    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
    )
    input_ids = encoded.input_ids if hasattr(encoded, "input_ids") else encoded
    if input_ids.ndim == 1:
        input_ids = input_ids.unsqueeze(0)
    input_ids = input_ids.to("cuda:0")

    with torch.inference_mode():
        generated = model.generate(
            input_ids=input_ids,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    response = tokenizer.decode(generated[0, input_ids.shape[1] :], skip_special_tokens=True).strip()
    print(response)


if __name__ == "__main__":
    main()
