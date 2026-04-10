"""Benchmark the new expert-adapter battery strategy against the old prompt-only battery strategy."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
import statistics
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.battery import BatteryMatrix, ExpertProfile, dispatch_expert, load_expert_profiles
from lume.evaluation import generate_text


@dataclass(slots=True)
class StrategyExampleResult:
    dataset: str
    task_id: str
    action_label: str
    old_strategy_length: int
    new_strategy_length: int
    old_char_match: float
    new_char_match: float
    old_similarity: float
    new_similarity: float
    old_prefix_match: bool
    new_prefix_match: bool
    winner: str
    old_primary_expert: str
    new_primary_expert: str
    new_cascade: list[str]
    target_preview: str
    old_preview: str
    new_preview: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-root", default=str(ROOT / "data" / "datasets_v5_battery"))
    parser.add_argument("--battery-matrix-config", default=str(ROOT / "configs" / "battery_matrix.yaml"))
    parser.add_argument("--expert-report", default=str(ROOT / "data" / "reports" / "expert_adapter_pipeline_report.json"))
    parser.add_argument("--fallback-model-root", default=str(ROOT / "data" / "distilled" / "transformers-lora-v5-battery-two-stage"))
    parser.add_argument("--max-examples-per-dataset", type=int, default=4)
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--output-json",
        default=str(ROOT / "data" / "reports" / "new_vs_old_battery_2026-04-10.json"),
    )
    parser.add_argument(
        "--output-md",
        default=str(ROOT / "data" / "reports" / "new_vs_old_battery_2026-04-10.md"),
    )
    return parser.parse_args()


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
        if len(records) >= limit:
            break
    return records


def _target_text(record: dict[str, Any]) -> str:
    target = record.get("target", "")
    if isinstance(target, dict):
        return str(target.get("ideal_reply", "")).strip()
    if isinstance(target, list):
        return json.dumps(target, ensure_ascii=False)
    return str(target).strip()


def _action_label(record: dict[str, Any]) -> str:
    target = record.get("target", "")
    if isinstance(target, dict):
        return str(target.get("action_label", "unknown"))
    return "unknown"


def _preview(text: str, limit: int = 160) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _char_match(prediction: str, target: str) -> float:
    compare_len = max(1, min(len(prediction), len(target)))
    match_count = sum(
        1 for index in range(compare_len)
        if prediction[index:index + 1] == target[index:index + 1]
    )
    return round(match_count / compare_len, 4)


def _prefix_match(prediction: str, target: str) -> bool:
    if not prediction or not target:
        return False
    return prediction.startswith(target[: min(12, len(target))])


def _similarity(prediction: str, target: str) -> float:
    if not prediction or not target:
        return 0.0
    return round(SequenceMatcher(None, prediction, target).ratio(), 4)


def _winner(old_char_match: float, new_char_match: float, old_similarity: float, new_similarity: float) -> str:
    old_score = old_char_match + old_similarity
    new_score = new_char_match + new_similarity
    if abs(old_score - new_score) < 1e-6:
        return "tie"
    return "new" if new_score > old_score else "old"


def _build_old_task(input_text: str) -> str:
    return (
        "Continue the active software task using the current worksite state below. "
        "Return only the next best response.\n\n"
        f"{input_text}"
    )


def _compact_task_input(input_text: str) -> str:
    keep_keys = {
        "Prompt_Role",
        "Current_Request",
        "Previous_Goal",
        "Last_Status",
        "Route_Mode",
        "Pending_Task",
        "Current_Focus",
        "Recent_File",
        "Recent_Command_Result",
        "Last_Assistant",
        "Notes_Summary",
        "Task",
    }
    lines: list[str] = []
    for raw_line in str(input_text).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key not in keep_keys:
            continue
        lines.append(f"{key}: {_preview(value.strip(), 120)}")
    compact = "\n".join(lines).strip()
    return compact or _preview(input_text, 800)


def _build_new_prompt(task: str, expert: ExpertProfile, previous_output: str = "", context_report: str | None = None) -> str:
    if not previous_output:
        return (
            f"You are the '{expert.name}' expert battery for domain '{expert.domain}'.\n"
            f"Description: {expert.description}\n"
            f"{context_report + chr(10) if context_report else ''}"
            f"Task: {task}\n"
            "Produce a concise local-first plan or answer that fits the current task."
        )
    return (
        f"You are the '{expert.name}' expert battery for domain '{expert.domain}'.\n"
        f"Description: {expert.description}\n"
        f"{context_report + chr(10) if context_report else ''}"
        f"Task: {task}\n"
        f"Primary local draft:\n{previous_output}\n\n"
        "Refine, tighten, or extend the draft from your domain perspective. "
        "Return only the improved local result."
    )


def _load_expert_model_roots(report_path: Path) -> dict[str, Path]:
    payload = json.loads(report_path.read_text("utf-8"))
    model_roots: dict[str, Path] = {}
    for expert_name, item in payload.get("experts", {}).items():
        if isinstance(item, dict) and item.get("model_root"):
            model_roots[expert_name] = Path(str(item["model_root"]))
    return model_roots


def _run_new_strategy(
    *,
    task: str,
    experts: list[ExpertProfile],
    expert_model_roots: dict[str, Path],
    fallback_model_root: Path,
    device: str,
) -> tuple[str, str, list[str]]:
    compact_task = _compact_task_input(task)
    dispatch = dispatch_expert(compact_task, experts)
    previous_output = ""
    cascade_names = [expert.name for expert in dispatch.cascade_experts]
    for expert in dispatch.cascade_experts:
        model_root = expert_model_roots.get(expert.name, fallback_model_root)
        prompt = _build_new_prompt(compact_task, expert, previous_output=previous_output)
        generated = generate_text(model_root, f"User:\n{prompt}\n\nAssistant:\n", device=device)
        previous_output = generated.split("Assistant:\n", 1)[-1].strip() or generated.strip()
    return previous_output, dispatch.primary_expert.name, cascade_names


def _summarize(values: list[StrategyExampleResult]) -> dict[str, Any]:
    return {
        "example_count": len(values),
        "old_avg_char_match": round(statistics.mean(item.old_char_match for item in values), 4),
        "new_avg_char_match": round(statistics.mean(item.new_char_match for item in values), 4),
        "old_avg_similarity": round(statistics.mean(item.old_similarity for item in values), 4),
        "new_avg_similarity": round(statistics.mean(item.new_similarity for item in values), 4),
        "old_prefix_match_rate": round(sum(1 for item in values if item.old_prefix_match) / len(values), 4),
        "new_prefix_match_rate": round(sum(1 for item in values if item.new_prefix_match) / len(values), 4),
        "old_avg_length": round(statistics.mean(item.old_strategy_length for item in values), 2),
        "new_avg_length": round(statistics.mean(item.new_strategy_length for item in values), 2),
        "new_win_count": sum(1 for item in values if item.winner == "new"),
        "old_win_count": sum(1 for item in values if item.winner == "old"),
        "tie_count": sum(1 for item in values if item.winner == "tie"),
    }


def _build_markdown_report(
    *,
    dataset_summaries: dict[str, dict[str, Any]],
    overall_summary: dict[str, Any],
    examples: list[StrategyExampleResult],
    report_path: Path,
) -> str:
    lines = [
        "# New vs Old Battery Strategy Benchmark",
        "",
        f"- Expert Report: `{report_path}`",
        f"- Total Matched Examples: `{overall_summary['example_count']}`",
        "",
        "## Headline",
        "",
        f"- New avg char match: `{overall_summary['new_avg_char_match']}` vs old `{overall_summary['old_avg_char_match']}`",
        f"- New avg similarity: `{overall_summary['new_avg_similarity']}` vs old `{overall_summary['old_avg_similarity']}`",
        f"- New prefix match rate: `{overall_summary['new_prefix_match_rate']}` vs old `{overall_summary['old_prefix_match_rate']}`",
        f"- New wins: `{overall_summary['new_win_count']}` / Old wins: `{overall_summary['old_win_count']}` / Ties: `{overall_summary['tie_count']}`",
        "",
        "## Per Dataset",
        "",
        "| Dataset | Examples | New Char Match | Old Char Match | New Similarity | Old Similarity | New Wins | Old Wins |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_name, summary in dataset_summaries.items():
        lines.append(
            f"| `{dataset_name}` | {summary['example_count']} | {summary['new_avg_char_match']} | "
            f"{summary['old_avg_char_match']} | {summary['new_avg_similarity']} | {summary['old_avg_similarity']} | "
            f"{summary['new_win_count']} | {summary['old_win_count']} |"
        )

    win_examples = [item for item in examples if item.winner == "new"][:5]
    if win_examples:
        lines.extend(["", "## New Strategy Win Samples", ""])
        for item in win_examples:
            lines.extend(
                [
                    f"### `{item.dataset}` · `{item.task_id}`",
                    f"- Action Label: `{item.action_label}`",
                    f"- Old Expert: `{item.old_primary_expert}`",
                    f"- New Expert: `{item.new_primary_expert}`",
                    f"- New Cascade: `{' -> '.join(item.new_cascade)}`",
                    f"- Target: `{item.target_preview}`",
                    f"- Old: `{item.old_preview}`",
                    f"- New: `{item.new_preview}`",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    datasets_root = Path(args.datasets_root)
    battery_matrix = BatteryMatrix(config_path=Path(args.battery_matrix_config))
    if not battery_matrix.available:
        raise RuntimeError("Old battery strategy is not available through Ollama.")
    experts = load_expert_profiles(Path(args.battery_matrix_config))
    expert_model_roots = _load_expert_model_roots(Path(args.expert_report))
    fallback_model_root = Path(args.fallback_model_root)

    dataset_paths = {
        "continue": datasets_root / "codex_continue_eval.jsonl",
        "patch": datasets_root / "codex_patch_eval.jsonl",
        "log": datasets_root / "codex_log_eval.jsonl",
    }

    results: list[StrategyExampleResult] = []
    grouped: dict[str, list[StrategyExampleResult]] = {key: [] for key in dataset_paths}
    for dataset_name, path in dataset_paths.items():
        for record in _read_jsonl(path, args.max_examples_per_dataset):
            input_text = str(record.get("input", "")).strip()
            target_text = _target_text(record)
            if not input_text or not target_text:
                continue

            old_result = battery_matrix.complete(_build_old_task(input_text))
            old_reply = old_result.output.strip()
            new_reply, new_primary_expert, new_cascade = _run_new_strategy(
                task=_build_old_task(input_text),
                experts=experts,
                expert_model_roots=expert_model_roots,
                fallback_model_root=fallback_model_root,
                device=args.device,
            )
            old_char_match = _char_match(old_reply, target_text)
            new_char_match = _char_match(new_reply, target_text)
            old_similarity = _similarity(old_reply, target_text)
            new_similarity = _similarity(new_reply, target_text)
            example = StrategyExampleResult(
                dataset=dataset_name,
                task_id=str(record.get("task_id", "")),
                action_label=_action_label(record),
                old_strategy_length=len(old_reply),
                new_strategy_length=len(new_reply),
                old_char_match=old_char_match,
                new_char_match=new_char_match,
                old_similarity=old_similarity,
                new_similarity=new_similarity,
                old_prefix_match=_prefix_match(old_reply, target_text),
                new_prefix_match=_prefix_match(new_reply, target_text),
                winner=_winner(old_char_match, new_char_match, old_similarity, new_similarity),
                old_primary_expert=old_result.dispatch.primary_expert.name,
                new_primary_expert=new_primary_expert,
                new_cascade=new_cascade,
                target_preview=_preview(target_text),
                old_preview=_preview(old_reply),
                new_preview=_preview(new_reply),
            )
            results.append(example)
            grouped[dataset_name].append(example)

    dataset_summaries = {name: _summarize(items) for name, items in grouped.items() if items}
    overall_summary = _summarize(results)
    payload = {
        "datasets_root": str(datasets_root),
        "expert_report": args.expert_report,
        "fallback_model_root": str(fallback_model_root),
        "max_examples_per_dataset": args.max_examples_per_dataset,
        "dataset_summaries": dataset_summaries,
        "overall_summary": overall_summary,
        "example_results": [asdict(item) for item in results],
    }
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    output_md.write_text(
        _build_markdown_report(
            dataset_summaries=dataset_summaries,
            overall_summary=overall_summary,
            examples=results,
            report_path=Path(args.expert_report),
        ),
        "utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(output_json)
    print(output_md)


if __name__ == "__main__":
    main()
