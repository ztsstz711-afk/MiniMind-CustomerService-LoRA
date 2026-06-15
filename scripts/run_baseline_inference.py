"""Run MiniMind baseline inference on fixed customer-service prompts.

This script lives outside the MiniMind source tree and does not modify upstream code.
"""

import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINIMIND_ROOT = PROJECT_ROOT / "minimind"
CHECKPOINT_PATH = MINIMIND_ROOT / "out" / "full_sft_768.pth"
TOKENIZER_PATH = MINIMIND_ROOT / "model"
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"
MARKDOWN_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "baseline_outputs.md"
JSONL_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "baseline_outputs.jsonl"

HIDDEN_SIZE = 768
NUM_HIDDEN_LAYERS = 8
USE_MOE = False
MAX_NEW_TOKENS = 220
TEMPERATURE = 0.7
TOP_P = 0.9


def add_minimind_to_path() -> None:
    minimind_path = str(MINIMIND_ROOT)
    if minimind_path not in sys.path:
        sys.path.insert(0, minimind_path)


def validate_inputs() -> None:
    required_paths = [
        CHECKPOINT_PATH,
        TOKENIZER_PATH / "tokenizer.json",
        TOKENIZER_PATH / "tokenizer_config.json",
        PROMPTS_PATH,
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        rendered = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required inference file(s):\n{rendered}")


def load_prompts() -> list[dict[str, str]]:
    prompts = []
    with PROMPTS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {PROMPTS_PATH} at line {line_number}")
            record = json.loads(line)
            if not isinstance(record, dict) or not {"category", "prompt"} <= record.keys():
                raise ValueError(
                    f"Invalid prompt record at line {line_number}: "
                    "required fields are category and prompt"
                )
            prompts.append(
                {
                    "category": str(record["category"]).strip(),
                    "prompt": str(record["prompt"]).strip(),
                }
            )
    if not prompts:
        raise ValueError(f"No prompts found in {PROMPTS_PATH}")
    return prompts


def load_model(device: str):
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
        state_dict = torch.load(CHECKPOINT_PATH, map_location=device)
        model.load_state_dict(state_dict, strict=True)
    except Exception as exc:
        raise RuntimeError(
            "Failed to load MiniMind checkpoint. Check that "
            f"{CHECKPOINT_PATH} matches hidden_size={HIDDEN_SIZE}, "
            f"num_hidden_layers={NUM_HIDDEN_LAYERS}, use_moe={USE_MOE}. "
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


def write_outputs(records: list[dict[str, object]], device: str) -> None:
    JSONL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with JSONL_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    lines = [
        "# MiniMind Baseline Outputs",
        "",
        f"- checkpoint: `{CHECKPOINT_PATH}`",
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
                f"## {index}. {record['category']}",
                "",
                "**Prompt**",
                "",
                str(record["prompt"]),
                "",
                "**Model Output**",
                "",
                str(record["model_output"]),
                "",
            ]
        )
    MARKDOWN_OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    validate_inputs()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    print(f"Tokenizer: {TOKENIZER_PATH}")

    prompts = load_prompts()
    model, tokenizer = load_model(device)

    records = []
    for index, item in enumerate(prompts, start=1):
        start = time.time()
        print(f"[{index}/{len(prompts)}] {item['category']}")
        output = generate_response(model, tokenizer, item["prompt"], device)
        records.append(
            {
                "category": item["category"],
                "prompt": item["prompt"],
                "model_output": output,
                "elapsed_seconds": round(time.time() - start, 3),
            }
        )

    write_outputs(records, device)
    print(f"Markdown saved to: {MARKDOWN_OUTPUT_PATH}")
    print(f"JSONL saved to: {JSONL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
