"""Build and generate the private, frozen Qwen v7 evaluation set.

The source test dialogue and generated replies stay under ignored ``outputs/``.
The script enforces one case per source dialogue group, stratifies the existing
real test split, and records hashes/configuration so later judging cannot quietly
change the prompt set or decoding settings.

This creates evaluation material only.  It does not score quality and does not
call an external judge API.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from qwen35_utils import allocate_strata, generate_rows, load_rows, require_packages, stable_case_id


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT / "models" / "qwen3_5_4b"
DEFAULT_TEST_FILE = ROOT / "outputs" / "qwen35_dch2_protocol_v8" / "frozen_external_cases.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen35_frozen_eval"
DEFAULT_CONDITIONS = {"B0": None}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def choose_group_disjoint_rows(rows: list[dict], sample_size: int, seed: str) -> tuple[list[dict], dict[str, int]]:
    """Take a stratified deterministic sample with no repeated source dialogue."""
    counts = Counter(row["category"] for row in rows)
    allocation = allocate_strata(counts, sample_size)
    strata: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        strata[row["category"]].append(row)

    selected: list[dict] = []
    used_groups: set[str] = set()
    # Scarce strata go first so broad categories cannot consume their groups.
    for category in sorted(strata, key=lambda value: (len({row["source_dialogue_group"] for row in strata[value]}), value)):
        ordered = sorted(strata[category], key=stable_case_id)
        random.Random(f"{seed}:{category}").shuffle(ordered)
        picked: list[dict] = []
        for row in ordered:
            if row["source_dialogue_group"] in used_groups:
                continue
            picked.append(row)
            used_groups.add(row["source_dialogue_group"])
            if len(picked) == allocation[category]:
                break
        if len(picked) != allocation[category]:
            raise ValueError(f"Could not allocate {allocation[category]} group-disjoint rows for {category}")
        selected.extend(picked)

    selected.sort(key=stable_case_id)
    if len(selected) != sample_size or len({row["source_dialogue_group"] for row in selected}) != sample_size:
        raise AssertionError("Frozen selection is not group-disjoint")
    return selected, dict(sorted(allocation.items()))


def parse_condition(value: str) -> tuple[str, Path | None]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("condition must use CONDITION_ID=BASE or CONDITION_ID=ADAPTER_PATH")
    condition_id, location = value.split("=", 1)
    if not condition_id or not location:
        raise argparse.ArgumentTypeError("condition ID and location are required")
    return condition_id, None if location.upper() == "BASE" else Path(location)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a group-disjoint frozen Qwen evaluation and generate condition outputs.")
    parser.add_argument("--model_name_or_path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--test_file", type=Path, default=DEFAULT_TEST_FILE)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sample_size", type=int, default=120)
    parser.add_argument("--seed", default="qwen-v7-frozen-20260927")
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--prepare_only", action="store_true", help="Freeze cases only; do not load the model or generate outputs.")
    parser.add_argument("--rebuild_selection", action="store_true", help="Replace an existing private selection after explicitly changing its protocol.")
    parser.add_argument(
        "--condition",
        action="append",
        type=parse_condition,
        help="Repeatable CONDITION_ID=BASE or CONDITION_ID=ADAPTER_PATH. Defaults to the base model only.",
    )
    return parser.parse_args()


def selection_metadata(rows: list[dict], args: argparse.Namespace) -> dict:
    case_ids = [stable_case_id(row) for row in rows]
    return {
        "protocol": "qwen_frozen_group_disjoint_eval_v7",
        "purpose": "private fixed generation set; no quality score or winner is implied",
        "test_file": str(args.test_file),
        "test_file_sha256": sha256_file(args.test_file),
        "sample_size": len(rows),
        "seed": args.seed,
        "category_counts": dict(sorted(Counter(row["category"] for row in rows).items())),
        "unique_source_dialogue_groups": len({row["source_dialogue_group"] for row in rows}),
        "case_ids_sha256": hashlib.sha256("\n".join(case_ids).encode("utf-8")).hexdigest(),
        "decoding": {"do_sample": False, "max_new_tokens": args.max_new_tokens},
        "boundary": "Cases are held out from training. Category labels stratify sampling only; they are not automatic quality labels.",
    }


def prepare_cases(args: argparse.Namespace) -> tuple[list[dict], dict]:
    cases_path = args.output_dir / "frozen_cases.jsonl"
    metadata_path = args.output_dir / "selection_metadata.json"
    if cases_path.exists() and not args.rebuild_selection:
        rows = read_jsonl(cases_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("test_file_sha256") != sha256_file(args.test_file):
            raise ValueError("Existing frozen set does not match the current test file; use a new output directory or --rebuild_selection.")
        if len(rows) != metadata.get("sample_size") or len({row["source_dialogue_group"] for row in rows}) != len(rows):
            raise ValueError("Existing frozen set violates its group-disjoint contract")
        return rows, metadata

    rows = load_rows(args.test_file)
    selected, _ = choose_group_disjoint_rows(rows, args.sample_size, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(cases_path, selected)
    metadata = selection_metadata(selected, args)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return selected, metadata


def generate_condition_outputs(args: argparse.Namespace, rows: list[dict], metadata: dict, conditions: dict[str, Path | None]) -> None:
    output_path = args.output_dir / "condition_outputs.jsonl"
    generation_path = args.output_dir / "generation_metadata.json"
    if output_path.exists():
        raise FileExistsError(f"Refusing to mix outputs in an existing frozen run: {output_path}")
    if not args.model_name_or_path.is_dir():
        raise FileNotFoundError(f"Model path missing: {args.model_name_or_path}")
    for condition_id, adapter_path in conditions.items():
        if adapter_path is not None and not adapter_path.is_dir():
            raise FileNotFoundError(f"Adapter for {condition_id} missing: {adapter_path}")

    torch, _, _, _, _, _, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig = require_packages()
    from transformers import AutoConfig, AutoModelForImageTextToText
    from peft import PeftModel

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for frozen evaluation generation")
    tokenizer = AutoTokenizer.from_pretrained(str(args.model_name_or_path), trust_remote_code=True, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )

    architecture = AutoConfig.from_pretrained(str(args.model_name_or_path), local_files_only=True).model_type
    model_loader = AutoModelForImageTextToText if architecture == "qwen3_5" else AutoModelForCausalLM

    def load_clean_base():
        base_model = model_loader.from_pretrained(
            str(args.model_name_or_path),
            quantization_config=quantization_config,
            device_map={"": 0},
            trust_remote_code=True,
            local_files_only=True,
        )
        base_model.config.use_cache = True
        return base_model

    def generate_qwen35_rows(model, tokenizer, rows: list[dict]) -> dict[str, str]:
        """Generate final answers with Qwen3.5 thinking explicitly disabled.

        Qwen3.5 otherwise opens an unclosed ``<think>`` block by default.  With
        a bounded 128-token decode, the base arm can expose only reasoning and
        never reach a customer-facing answer, making a base-vs-adapter comparison
        invalid.  The template flag is applied identically to every condition;
        decoding itself remains greedy with the registered token limit.
        """
        model.eval()
        results: dict[str, str] = {}
        with torch.inference_mode():
            for index, row in enumerate(rows, start=1):
                encoded = tokenizer.apply_chat_template(
                    row["messages"][:-1],
                    tokenize=True,
                    add_generation_prompt=True,
                    enable_thinking=False,
                    return_tensors="pt",
                )
                input_ids = encoded.input_ids if hasattr(encoded, "input_ids") else encoded
                if input_ids.ndim == 1:
                    input_ids = input_ids.unsqueeze(0)
                input_ids = input_ids.to("cuda:0")
                generated = model.generate(
                    input_ids=input_ids,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
                results[stable_case_id(row)] = tokenizer.decode(
                    generated[0, input_ids.shape[1]:], skip_special_tokens=True
                ).strip()
                if index % 10 == 0 or index == len(rows):
                    print(f"generated {index}/{len(rows)}", flush=True)
        return results

    output_rows: list[dict] = []
    try:
        for condition_id, adapter_path in conditions.items():
            print(f"generating {condition_id} ({len(rows)} cases)", flush=True)
            # A PeftModel mutates the base module when attaching an adapter.
            # Reload it for every condition so no adapter can leak into another arm.
            base = load_clean_base()
            model = base if adapter_path is None else PeftModel.from_pretrained(base, str(adapter_path), local_files_only=True)
            model.config.use_cache = True
            generated = (
                generate_qwen35_rows(model, tokenizer, rows)
                if architecture == "qwen3_5"
                else generate_rows(model, tokenizer, rows, args.max_new_tokens, torch)
            )
            output_rows.extend(
                {"case_id": stable_case_id(row), "condition_id": condition_id, "response": generated[stable_case_id(row)]}
                for row in rows
            )
            del model, base
            gc.collect()
            torch.cuda.empty_cache()
    finally:
        del tokenizer
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_path, output_rows)
    generation_metadata = {
        **metadata,
        "model_name_or_path": str(args.model_name_or_path),
        "conditions": {condition_id: "base" if adapter_path is None else str(adapter_path) for condition_id, adapter_path in conditions.items()},
        "condition_loading": "fresh quantized base model loaded separately for every condition; adapters are never stacked",
        "model_architecture": architecture,
        "qwen35_thinking": "disabled for all conditions" if architecture == "qwen3_5" else "not_applicable",
        "output_rows": len(output_rows),
        "output_sha256": sha256_file(output_path),
        "boundary": "Generated answers are private evaluation material. No automatic judge or human result has been computed.",
    }
    generation_path.write_text(json.dumps(generation_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not args.test_file.is_file():
        raise FileNotFoundError(f"Test file missing: {args.test_file}")
    rows, metadata = prepare_cases(args)
    print(json.dumps({"frozen_cases": len(rows), "metadata": metadata}, ensure_ascii=False), flush=True)
    if args.prepare_only:
        return
    conditions = dict(args.condition) if args.condition else DEFAULT_CONDITIONS
    if len(conditions) < 2:
        raise ValueError("At least two conditions are required for comparison")
    generate_condition_outputs(args, rows, metadata, conditions)
    print(json.dumps({"output_dir": str(args.output_dir), "conditions": list(conditions), "generation_complete": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
