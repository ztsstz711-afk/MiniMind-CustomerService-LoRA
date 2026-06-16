"""Run Qwen2.5 LoRA v4 inference on the 100 v3 eval prompts."""

import argparse
import json
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "qwen2_5_1_5b_instruct"
DEFAULT_ADAPTER_PATH = PROJECT_ROOT / "outputs" / "qwen2_5_1_5b_lora_v4"
DEFAULT_EVAL_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"
DEFAULT_JSONL_OUTPUT = PROJECT_ROOT / "outputs" / "eval_outputs_qwen_lora_v4.jsonl"
DEFAULT_MARKDOWN_OUTPUT = PROJECT_ROOT / "experiments" / "eval_outputs_qwen_lora_v4.md"
MODEL_NAME = "qwen2_5_1_5b_lora_v4"

SYSTEM_PROMPT = (
    "你是一个专业、礼貌、遵守平台规则的电商售后客服助手。"
    "你需要根据用户问题给出清晰、合规、不过度承诺的回复。"
    "遇到违规、不合理或无法确认的信息请求时，应礼貌拒绝，并给出合规替代方案。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Qwen2.5 LoRA v4 eval inference.")
    parser.add_argument("--model_name_or_path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--adapter_path", type=Path, default=DEFAULT_ADAPTER_PATH)
    parser.add_argument("--eval_path", type=Path, default=DEFAULT_EVAL_PATH)
    parser.add_argument("--output_path", type=Path, default=DEFAULT_JSONL_OUTPUT)
    parser.add_argument("--markdown_path", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--max_new_tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.9)
    return parser.parse_args()


def print_cuda_memory(prefix: str) -> None:
    if not torch.cuda.is_available():
        print(f"{prefix} CUDA memory: no cuda")
        return
    allocated = torch.cuda.memory_allocated() / (1024**3)
    reserved = torch.cuda.memory_reserved() / (1024**3)
    print(f"{prefix} CUDA memory allocated: {allocated:.3f} GB")
    print(f"{prefix} CUDA memory reserved: {reserved:.3f} GB")


def read_eval_prompts(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing eval prompt file: {path}")
    required = {
        "id",
        "category",
        "prompt",
        "expected_behavior",
        "required_elements",
        "forbidden_elements",
        "difficulty",
        "tags",
    }
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            missing = required - set(record)
            if missing:
                raise ValueError(f"Line {line_number} missing fields: {sorted(missing)}")
            rows.append(record)
    return rows


def make_messages(prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


@torch.inference_mode()
def generate(model, tokenizer, prompt: str, args: argparse.Namespace) -> str:
    input_text = tokenizer.apply_chat_template(
        make_messages(prompt),
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=args.max_new_tokens,
        do_sample=True,
        temperature=args.temperature,
        top_p=args.top_p,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    generated = output_ids[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def write_outputs(rows: list[dict], args: argparse.Namespace) -> None:
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with args.output_path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# Qwen LoRA v4 Eval Outputs",
        "",
        f"- base model: `{args.model_name_or_path}`",
        f"- adapter: `{args.adapter_path}`",
        f"- eval prompts: `{args.eval_path}`",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend([
            f"## {index}. {row['id']} {row['category']} ({row['difficulty']})",
            "",
            "**Prompt**",
            "",
            row["prompt"],
            "",
            "**Output**",
            "",
            row["output"],
            "",
        ])
    args.markdown_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Qwen LoRA v4 eval inference.")
    if not args.model_name_or_path.is_dir():
        raise FileNotFoundError(f"Missing local base model: {args.model_name_or_path}")
    if not args.adapter_path.is_dir():
        raise FileNotFoundError(f"Missing LoRA adapter directory: {args.adapter_path}")

    prompts = read_eval_prompts(args.eval_path)
    print(f"Base model: {args.model_name_or_path}")
    print(f"LoRA adapter: {args.adapter_path}")
    print(f"Eval prompts: {args.eval_path}")
    print_cuda_memory("Before load")

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model_name_or_path),
        trust_remote_code=True,
        local_files_only=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = AutoModelForCausalLM.from_pretrained(
        str(args.model_name_or_path),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    )
    model = PeftModel.from_pretrained(base_model, str(args.adapter_path), local_files_only=True).eval()
    print_cuda_memory("After load")

    outputs = []
    for index, item in enumerate(prompts, start=1):
        start = time.time()
        print(f"[{index}/{len(prompts)}] {item['id']} {item['category']}")
        output = generate(model, tokenizer, item["prompt"], args)
        outputs.append({
            "id": item["id"],
            "category": item["category"],
            "prompt": item["prompt"],
            "expected_behavior": item["expected_behavior"],
            "required_elements": item["required_elements"],
            "forbidden_elements": item["forbidden_elements"],
            "difficulty": item["difficulty"],
            "tags": item["tags"],
            "model_name": MODEL_NAME,
            "output": output,
            "model_output": output,
            "elapsed_seconds": round(time.time() - start, 3),
        })

    write_outputs(outputs, args)
    print_cuda_memory("After inference")
    print(f"JSONL saved to: {args.output_path}")
    print(f"Markdown saved to: {args.markdown_path}")


if __name__ == "__main__":
    main()
