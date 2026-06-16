"""Run v3 evaluation inference for baseline, LoRA v1, or LoRA v2.

This script lives outside the MiniMind source tree and does not modify upstream code.
It writes separate v3 evaluation outputs and never overwrites earlier 10-prompt outputs.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINIMIND_ROOT = PROJECT_ROOT / "minimind"
BASE_CHECKPOINT_PATH = MINIMIND_ROOT / "out" / "full_sft_768.pth"
TOKENIZER_PATH = MINIMIND_ROOT / "model"
EVAL_PROMPTS_PATH = PROJECT_ROOT / "data" / "eval_prompts_v3.jsonl"

LORA_PATHS = {
    "baseline": None,
    "lora_v1": PROJECT_ROOT / "outputs" / "lora_customer_service" / "lora_customer_service_768.pth",
    "lora_v2": PROJECT_ROOT / "outputs" / "lora_customer_service_v2" / "lora_customer_service_v2_768.pth",
}

HIDDEN_SIZE = 768
NUM_HIDDEN_LAYERS = 8
USE_MOE = False
MAX_NEW_TOKENS = 220
TEMPERATURE = 0.7
TOP_P = 0.9


def output_paths(model_name: str) -> tuple[Path, Path]:
    return (
        PROJECT_ROOT / "outputs" / f"eval_outputs_{model_name}_v3.jsonl",
        PROJECT_ROOT / "experiments" / f"eval_outputs_{model_name}_v3.md",
    )


def add_minimind_to_path() -> None:
    minimind_path = str(MINIMIND_ROOT)
    if minimind_path not in sys.path:
        sys.path.insert(0, minimind_path)


def validate_inputs(model_name: str) -> None:
    required_paths = [
        BASE_CHECKPOINT_PATH,
        TOKENIZER_PATH / "tokenizer.json",
        TOKENIZER_PATH / "tokenizer_config.json",
        EVAL_PROMPTS_PATH,
    ]
    lora_path = LORA_PATHS[model_name]
    if lora_path is not None:
        required_paths.append(lora_path)
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        rendered = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required inference file(s):\n{rendered}")


def load_eval_prompts() -> list[dict]:
    prompts = []
    required_fields = {
        "id",
        "category",
        "prompt",
        "expected_behavior",
        "required_elements",
        "forbidden_elements",
        "difficulty",
        "tags",
    }
    with EVAL_PROMPTS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {EVAL_PROMPTS_PATH} at line {line_number}")
            record = json.loads(line)
            missing = required_fields - set(record)
            if missing:
                raise ValueError(
                    f"Invalid eval prompt at line {line_number}; missing {sorted(missing)}"
                )
            prompts.append(record)
    if len(prompts) != 100:
        raise ValueError(f"Expected 100 eval prompts, got {len(prompts)}")
    return prompts


def load_model(model_name: str, device: str):
    add_minimind_to_path()
    from model.model_minimind import MiniMindConfig, MiniMindForCausalLM

    tokenizer = AutoTokenizer.from_pretrained(str(TOKENIZER_PATH))
    config = MiniMindConfig(
        hidden_size=HIDDEN_SIZE,
        num_hidden_layers=NUM_HIDDEN_LAYERS,
        use_moe=USE_MOE,
    )
    model = MiniMindForCausalLM(config)
    try:
        base_state = torch.load(BASE_CHECKPOINT_PATH, map_location=device)
        model.load_state_dict(base_state, strict=True)
        lora_path = LORA_PATHS[model_name]
        if lora_path is not None:
            from model.model_lora import apply_lora, load_lora

            apply_lora(model)
            load_lora(model, str(lora_path))
    except Exception as exc:
        raise RuntimeError(
            "Failed to load MiniMind model for v3 evaluation. "
            f"model_name={model_name}, hidden_size={HIDDEN_SIZE}, "
            f"num_hidden_layers={NUM_HIDDEN_LAYERS}, use_moe={USE_MOE}, "
            f"base={BASE_CHECKPOINT_PATH}, lora={LORA_PATHS[model_name]}. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    model = model.half().eval().to(device)
    return model, tokenizer


@torch.inference_mode()
def generate_response(model, tokenizer, prompt: str, device: str) -> str:
    conversation = [{"role": "user", "content": prompt}]
    input_text = tokenizer.apply_chat_template(
        conversation,
        tokenize=False,
        add_generation_prompt=True,
        open_thinking=False,
    )
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True).to(device)
    generated_ids = model.generate(
        inputs=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
        top_p=TOP_P,
        temperature=TEMPERATURE,
        repetition_penalty=1,
    )
    output_ids = generated_ids[0][len(inputs["input_ids"][0]):]
    return tokenizer.decode(output_ids, skip_special_tokens=True).strip()


def make_output_record(item: dict, model_name: str, output: str, elapsed_seconds: float) -> dict:
    return {
        "id": item["id"],
        "category": item["category"],
        "prompt": item["prompt"],
        "expected_behavior": item["expected_behavior"],
        "required_elements": item["required_elements"],
        "forbidden_elements": item["forbidden_elements"],
        "difficulty": item["difficulty"],
        "tags": item["tags"],
        "model_name": model_name,
        "output": output,
        "model_output": output,
        "elapsed_seconds": round(elapsed_seconds, 3),
    }


def write_outputs(records: list[dict], model_name: str, device: str) -> None:
    jsonl_path, markdown_path = output_paths(model_name)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    with jsonl_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    lines = [
        f"# Eval Outputs v3: {model_name}",
        "",
        f"- eval prompts: `{EVAL_PROMPTS_PATH}`",
        f"- base checkpoint: `{BASE_CHECKPOINT_PATH}`",
        f"- lora checkpoint: `{LORA_PATHS[model_name]}`",
        f"- tokenizer: `{TOKENIZER_PATH}`",
        f"- device: `{device}`",
        f"- max_new_tokens: `{MAX_NEW_TOKENS}`",
        f"- temperature: `{TEMPERATURE}`",
        f"- top_p: `{TOP_P}`",
        "",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"## {index}. {record['id']} {record['category']} ({record['difficulty']})",
                "",
                "**Prompt**",
                "",
                record["prompt"],
                "",
                "**Expected Behavior**",
                "",
                record["expected_behavior"],
                "",
                "**Model Output**",
                "",
                record["output"],
                "",
            ]
        )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v3 evaluation inference.")
    parser.add_argument("--model_name", required=True, choices=sorted(LORA_PATHS))
    args = parser.parse_args()

    validate_inputs(args.model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Model name: {args.model_name}")
    print(f"Base checkpoint: {BASE_CHECKPOINT_PATH}")
    print(f"LoRA checkpoint: {LORA_PATHS[args.model_name]}")
    print(f"Eval prompts: {EVAL_PROMPTS_PATH}")

    prompts = load_eval_prompts()
    model, tokenizer = load_model(args.model_name, device)

    records = []
    for index, item in enumerate(prompts, start=1):
        start = time.time()
        print(f"[{index}/{len(prompts)}] {item['id']} {item['category']}")
        output = generate_response(model, tokenizer, item["prompt"], device)
        records.append(make_output_record(item, args.model_name, output, time.time() - start))

    write_outputs(records, args.model_name, device)
    jsonl_path, markdown_path = output_paths(args.model_name)
    print(f"Markdown saved to: {markdown_path}")
    print(f"JSONL saved to: {jsonl_path}")


if __name__ == "__main__":
    main()
