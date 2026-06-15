"""Inspect MiniMind baseline inference requirements without loading a model."""

import ast
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINIMIND_ROOT = PROJECT_ROOT / "minimind"
EVAL_PATH = MINIMIND_ROOT / "eval_llm.py"
README_PATH = MINIMIND_ROOT / "README.md"
PROMPTS_PATH = PROJECT_ROOT / "data" / "baseline_prompts.jsonl"


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    print(f"Found: {path}")


def extract_argument_defaults(source: str) -> dict[str, object]:
    """Extract literal defaults from argparse add_argument calls."""
    defaults = {}
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue

        argument = node.args[0].value
        if not isinstance(argument, str) or not argument.startswith("--"):
            continue

        default_node = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "default"),
            None,
        )
        if default_node is None:
            continue
        try:
            defaults[argument.removeprefix("--")] = ast.literal_eval(default_node)
        except (ValueError, TypeError):
            defaults[argument.removeprefix("--")] = "<runtime expression>"
    return defaults


def inspect_source_requirements(source: str, defaults: dict[str, object]) -> None:
    required_fragments = {
        "tokenizer load": "AutoTokenizer.from_pretrained(args.load_from)",
        "checkpoint formula": "{args.weight}_{args.hidden_size}{moe_suffix}.pth",
        "LoRA load": "load_lora(model",
    }
    for label, fragment in required_fragments.items():
        if fragment not in source:
            raise ValueError(f"Could not find expected {label} logic in {EVAL_PATH}")

    load_from = str(defaults["load_from"])
    save_dir = str(defaults["save_dir"])
    weight = str(defaults["weight"])
    hidden_size = int(defaults["hidden_size"])
    use_moe = int(defaults["use_moe"])
    moe_suffix = "_moe" if use_moe else ""

    tokenizer_path = (MINIMIND_ROOT / load_from).resolve()
    checkpoint_path = (
        MINIMIND_ROOT
        / save_dir
        / f"{weight}_{hidden_size}{moe_suffix}.pth"
    ).resolve()

    print("Parsed eval_llm.py defaults:")
    for name in (
        "load_from",
        "save_dir",
        "weight",
        "lora_weight",
        "hidden_size",
        "num_hidden_layers",
        "use_moe",
        "max_new_tokens",
        "device",
    ):
        print(f"  {name}: {defaults.get(name, '<not found>')}")

    print(f"Possible tokenizer path: {tokenizer_path}")
    print(f"Tokenizer path exists: {tokenizer_path.is_dir()}")
    print(f"Possible checkpoint path: {checkpoint_path}")
    print(f"Checkpoint exists: {checkpoint_path.is_file()}")
    print(
        "Checkpoint naming formula: "
        "<save_dir>/<weight>_<hidden_size>[_moe].pth"
    )


def load_prompts(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Blank line in {path} at line {line_number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc
            if not isinstance(record, dict) or not {"category", "prompt"} <= record.keys():
                raise ValueError(
                    f"Invalid prompt record in {path} at line {line_number}: "
                    "required fields are category and prompt"
                )
            records.append(record)
    return records


def main() -> None:
    require_file(EVAL_PATH)
    require_file(README_PATH)
    require_file(PROMPTS_PATH)

    source = EVAL_PATH.read_text(encoding="utf-8")
    defaults = extract_argument_defaults(source)
    inspect_source_requirements(source, defaults)

    prompts = load_prompts(PROMPTS_PATH)
    print(f"Baseline prompt count: {len(prompts)}")
    print("Baseline inference requirements check completed.")


if __name__ == "__main__":
    main()
