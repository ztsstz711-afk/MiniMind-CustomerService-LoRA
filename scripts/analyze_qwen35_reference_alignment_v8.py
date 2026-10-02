"""Compare frozen generations with the supplied held-out assistant replies.

The metrics are deterministic task-alignment diagnostics. They measure literal
reference overlap and obvious output degeneration; they are not human
preference, business impact, or production-quality evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def case_id(row: dict) -> str:
    raw = f"{row['source_dialogue_group']}:{row['source_turn_index']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", str(text)).lower()


def lcs_length(left: str, right: str) -> int:
    if len(left) > len(right):
        left, right = right, left
    previous = [0] * (len(left) + 1)
    for right_char in right:
        current = [0]
        for index, left_char in enumerate(left, start=1):
            current.append(previous[index - 1] + 1 if left_char == right_char else max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def rouge_l_f1(candidate: str, reference: str) -> float:
    if not candidate or not reference:
        return 0.0
    lcs = lcs_length(candidate, reference)
    precision = lcs / len(candidate)
    recall = lcs / len(reference)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def ngram_f1(candidate: str, reference: str, n: int) -> float:
    candidate_counts = Counter(candidate[index:index + n] for index in range(max(0, len(candidate) - n + 1)))
    reference_counts = Counter(reference[index:index + n] for index in range(max(0, len(reference) - n + 1)))
    candidate_total = sum(candidate_counts.values())
    reference_total = sum(reference_counts.values())
    if not candidate_total or not reference_total:
        return 0.0
    overlap = sum((candidate_counts & reference_counts).values())
    precision = overlap / candidate_total
    recall = overlap / reference_total
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def repeated_ngram_fraction(text: str, n: int = 4) -> float:
    grams = [text[index:index + n] for index in range(max(0, len(text) - n + 1))]
    if not grams:
        return 0.0
    return 1.0 - len(set(grams)) / len(grams)


def bootstrap_interval(values: list[float], samples: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    estimates = sorted(mean(values[rng.randrange(len(values))] for _ in values) for _ in range(samples))
    return [estimates[int(0.025 * (samples - 1))], estimates[int(0.975 * (samples - 1))]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "outputs" / "qwen35_dch2_protocol_v8" / "frozen_external_cases.jsonl")
    parser.add_argument("--outputs", type=Path, default=ROOT / "outputs" / "qwen35_dch2_frozen_eval_v8_thinking_off" / "condition_outputs.jsonl")
    parser.add_argument("--output_dir", type=Path, default=ROOT / "outputs" / "qwen35_dch2_reference_alignment_v8")
    parser.add_argument("--base_condition", default="B0")
    parser.add_argument("--candidate_condition", default="R-DCH2")
    parser.add_argument("--bootstrap_samples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite: {args.output_dir}")
    cases = read_jsonl(args.cases)
    outputs = read_jsonl(args.outputs)
    references = {case_id(row): normalize(row["messages"][-1]["content"]) for row in cases}
    indexed = {(row["case_id"], row["condition_id"]): normalize(row["response"]) for row in outputs}
    expected = {(identifier, condition) for identifier in references for condition in (args.base_condition, args.candidate_condition)}
    if set(indexed) != expected:
        raise ValueError(f"Condition/case mismatch: missing={len(expected - set(indexed))}, extra={len(set(indexed) - expected)}")

    rows = []
    for identifier, reference in sorted(references.items()):
        for condition in (args.base_condition, args.candidate_condition):
            response = indexed[(identifier, condition)]
            rows.append({
                "case_id": identifier,
                "condition_id": condition,
                "reference_chars": len(reference),
                "response_chars": len(response),
                "absolute_length_error": abs(len(response) - len(reference)),
                "length_ratio": len(response) / len(reference) if reference else 0.0,
                "char_bigram_f1": ngram_f1(response, reference, 2),
                "rouge_l_f1": rouge_l_f1(response, reference),
                "empty": not response,
                "severe_length_collapse": bool(reference) and len(response) < max(4, 0.2 * len(reference)),
                "severe_length_expansion": bool(reference) and len(response) > max(40, 5 * len(reference)),
                "repeated_4gram_fraction": repeated_ngram_fraction(response),
            })

    by_condition = {condition: [row for row in rows if row["condition_id"] == condition] for condition in (args.base_condition, args.candidate_condition)}
    metrics = ("char_bigram_f1", "rouge_l_f1")
    conditions = {}
    for condition, condition_rows in by_condition.items():
        conditions[condition] = {
            "rows": len(condition_rows),
            "mean_char_bigram_f1": mean(row["char_bigram_f1"] for row in condition_rows),
            "mean_rouge_l_f1": mean(row["rouge_l_f1"] for row in condition_rows),
            "median_response_chars": median(row["response_chars"] for row in condition_rows),
            "median_reference_chars": median(row["reference_chars"] for row in condition_rows),
            "mean_absolute_length_error": mean(row["absolute_length_error"] for row in condition_rows),
            "empty_rows": sum(row["empty"] for row in condition_rows),
            "severe_length_collapse_rows": sum(row["severe_length_collapse"] for row in condition_rows),
            "severe_length_expansion_rows": sum(row["severe_length_expansion"] for row in condition_rows),
            "mean_repeated_4gram_fraction": mean(row["repeated_4gram_fraction"] for row in condition_rows),
        }

    by_key = {(row["case_id"], row["condition_id"]): row for row in rows}
    comparison = {}
    for metric in metrics:
        deltas = [by_key[(identifier, args.candidate_condition)][metric] - by_key[(identifier, args.base_condition)][metric] for identifier in sorted(references)]
        comparison[f"candidate_minus_base_{metric}"] = {
            "mean_delta": mean(deltas),
            "mean_delta_95_bootstrap_ci": bootstrap_interval(deltas, args.bootstrap_samples, args.seed),
            "cases_improved": sum(value > 0 for value in deltas),
            "cases_worsened": sum(value < 0 for value in deltas),
            "cases_tied": sum(value == 0 for value in deltas),
        }
    report = {
        "protocol": "qwen35_dch2_v8_reference_alignment",
        "cases": str(args.cases),
        "outputs": str(args.outputs),
        "unique_cases": len(references),
        "conditions": conditions,
        "comparison": comparison,
        "interpretation_rule": "Reference alignment is positive only when overlap deltas and their paired bootstrap intervals are above zero without severe degeneration increasing materially.",
        "boundary": "Deterministic literal-reference diagnostics only; not human preference, business impact, production quality, semantic equivalence, or generalized customer-service ability.",
    }
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "per_case_metrics.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    (args.output_dir / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
