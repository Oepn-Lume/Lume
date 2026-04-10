"""Benchmark pure Gemma vs the current battery model on action-task datasets."""

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

from lume.battery import BatteryMatrix
from lume.execution import OllamaLocalHandler


@dataclass(slots=True)
class ExampleResult:
    dataset: str
    task_id: str
    action_label: str
    target_length: int
    gemma_length: int
    battery_length: int
    gemma_char_match: float
    battery_char_match: float
    gemma_prefix_match: bool
    battery_prefix_match: bool
    gemma_similarity: float
    battery_similarity: float
    winner: str
    input_preview: str
    target_preview: str
    gemma_preview: str
    battery_preview: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets_v4"),
    )
    parser.add_argument(
        "--models-config",
        default=str(ROOT / "configs" / "models.yaml"),
    )
    parser.add_argument(
        "--battery-matrix-config",
        default=str(ROOT / "configs" / "battery_matrix.yaml"),
    )
    parser.add_argument("--max-examples-per-dataset", type=int, default=8)
    parser.add_argument(
        "--output-json",
        default=str(ROOT / "data" / "reports" / "battery_vs_gemma_action_benchmark_2026-04-10.json"),
    )
    parser.add_argument(
        "--output-md",
        default=str(ROOT / "data" / "reports" / "battery_vs_gemma_action_benchmark_2026-04-10.md"),
    )
    return parser.parse_args()


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in path.read_text("utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current_section = None
            else:
                data[key] = {}
                current_section = key
            continue
        if current_section and raw_line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            data[current_section][key.strip()] = value.strip().strip('"')
    return data


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


def _build_pure_gemma_prompt(input_text: str) -> str:
    return (
        "You are a local software-task assistant. "
        "Read the task context carefully and return only the best next response for the task. "
        "Be concise, actionable, and stay within the active task.\n\n"
        f"{input_text}"
    )


def _build_battery_task(input_text: str) -> str:
    return (
        "Continue the active software task using the current worksite state below. "
        "Return only the next best response.\n\n"
        f"{input_text}"
    )


def _preview(text: str, limit: int = 160) -> str:
    compact = " ".join(text.split())
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


def _summarize_results(values: list[ExampleResult]) -> dict[str, Any]:
    gemma_wins = sum(1 for item in values if item.winner == "gemma")
    battery_wins = sum(1 for item in values if item.winner == "battery")
    ties = sum(1 for item in values if item.winner == "tie")
    return {
        "example_count": len(values),
        "gemma_avg_char_match": round(statistics.mean(item.gemma_char_match for item in values), 4),
        "battery_avg_char_match": round(statistics.mean(item.battery_char_match for item in values), 4),
        "gemma_avg_similarity": round(statistics.mean(item.gemma_similarity for item in values), 4),
        "battery_avg_similarity": round(statistics.mean(item.battery_similarity for item in values), 4),
        "gemma_prefix_match_rate": round(
            sum(1 for item in values if item.gemma_prefix_match) / len(values), 4
        ),
        "battery_prefix_match_rate": round(
            sum(1 for item in values if item.battery_prefix_match) / len(values), 4
        ),
        "gemma_avg_length": round(statistics.mean(item.gemma_length for item in values), 2),
        "battery_avg_length": round(statistics.mean(item.battery_length for item in values), 2),
        "battery_win_count": battery_wins,
        "gemma_win_count": gemma_wins,
        "tie_count": ties,
    }


def _winner(
    *,
    gemma_char_match: float,
    battery_char_match: float,
    gemma_similarity: float,
    battery_similarity: float,
) -> str:
    gemma_score = gemma_char_match + gemma_similarity
    battery_score = battery_char_match + battery_similarity
    if abs(gemma_score - battery_score) < 1e-6:
        return "tie"
    return "battery" if battery_score > gemma_score else "gemma"


def _build_markdown_report(
    *,
    model_name: str,
    battery_config_path: Path,
    dataset_summaries: dict[str, dict[str, Any]],
    overall_summary: dict[str, Any],
    examples: list[ExampleResult],
) -> str:
    lines = [
        "# Battery Model vs Pure Gemma Benchmark",
        "",
        f"- Pure Gemma Model: `{model_name}`",
        f"- Battery Config: `{battery_config_path}`",
        f"- Dataset Families: `continue`, `patch`, `log`",
        f"- Total Matched Examples: `{overall_summary['example_count']}`",
        "",
        "## Headline",
        "",
        f"- Battery avg char match: `{overall_summary['battery_avg_char_match']}` vs Gemma `{overall_summary['gemma_avg_char_match']}`",
        f"- Battery avg similarity: `{overall_summary['battery_avg_similarity']}` vs Gemma `{overall_summary['gemma_avg_similarity']}`",
        f"- Battery prefix match rate: `{overall_summary['battery_prefix_match_rate']}` vs Gemma `{overall_summary['gemma_prefix_match_rate']}`",
        f"- Battery wins: `{overall_summary['battery_win_count']}` / Gemma wins: `{overall_summary['gemma_win_count']}` / Ties: `{overall_summary['tie_count']}`",
        "",
        "## Per Dataset",
        "",
        "| Dataset | Examples | Battery Char Match | Gemma Char Match | Battery Similarity | Gemma Similarity | Battery Wins | Gemma Wins |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset_name, summary in dataset_summaries.items():
        lines.append(
            f"| `{dataset_name}` | {summary['example_count']} | "
            f"{summary['battery_avg_char_match']} | {summary['gemma_avg_char_match']} | "
            f"{summary['battery_avg_similarity']} | {summary['gemma_avg_similarity']} | "
            f"{summary['battery_win_count']} | {summary['gemma_win_count']} |"
        )

    battery_examples = [item for item in examples if item.winner == "battery"][:5]
    if battery_examples:
        lines.extend(["", "## Battery Win Samples", ""])
        for item in battery_examples:
            lines.extend(
                [
                    f"### `{item.dataset}` · `{item.task_id}`",
                    f"- Action Label: `{item.action_label}`",
                    f"- Target: `{item.target_preview}`",
                    f"- Gemma: `{item.gemma_preview}`",
                    f"- Battery: `{item.battery_preview}`",
                    f"- Gemma Char Match: `{item.gemma_char_match}` / Battery Char Match: `{item.battery_char_match}`",
                    f"- Gemma Similarity: `{item.gemma_similarity}` / Battery Similarity: `{item.battery_similarity}`",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    datasets_root = Path(args.datasets_root)
    models_config = _parse_simple_yaml(Path(args.models_config))
    battery_config_path = Path(args.battery_matrix_config)
    local_config = models_config.get("local", {})
    model_name = str(local_config.get("base_model", local_config.get("battery_model_name", "gemma4:31b")))

    gemma = OllamaLocalHandler(model=model_name)
    battery = BatteryMatrix(config_path=battery_config_path)
    if not gemma.available:
        raise RuntimeError(f"Pure Gemma model '{model_name}' is not available in Ollama.")
    if not battery.available:
        raise RuntimeError("Battery model is not available through the configured Ollama setup.")

    dataset_paths = {
        "continue": datasets_root / "codex_continue_eval.jsonl",
        "patch": datasets_root / "codex_patch_eval.jsonl",
        "log": datasets_root / "codex_log_eval.jsonl",
    }
    example_results: list[ExampleResult] = []
    per_dataset_results: dict[str, list[ExampleResult]] = {key: [] for key in dataset_paths}

    for dataset_name, dataset_path in dataset_paths.items():
        records = _read_jsonl(dataset_path, args.max_examples_per_dataset)
        for record in records:
            input_text = str(record.get("input", "")).strip()
            target_text = _target_text(record)
            if not input_text or not target_text:
                continue

            gemma_reply = gemma.complete(_build_pure_gemma_prompt(input_text))
            battery_result = battery.complete(_build_battery_task(input_text))
            battery_reply = battery_result.output.strip()

            gemma_char_match = _char_match(gemma_reply, target_text)
            battery_char_match = _char_match(battery_reply, target_text)
            gemma_similarity = _similarity(gemma_reply, target_text)
            battery_similarity = _similarity(battery_reply, target_text)
            result = ExampleResult(
                dataset=dataset_name,
                task_id=str(record.get("task_id", "")),
                action_label=_action_label(record),
                target_length=len(target_text),
                gemma_length=len(gemma_reply),
                battery_length=len(battery_reply),
                gemma_char_match=gemma_char_match,
                battery_char_match=battery_char_match,
                gemma_prefix_match=_prefix_match(gemma_reply, target_text),
                battery_prefix_match=_prefix_match(battery_reply, target_text),
                gemma_similarity=gemma_similarity,
                battery_similarity=battery_similarity,
                winner=_winner(
                    gemma_char_match=gemma_char_match,
                    battery_char_match=battery_char_match,
                    gemma_similarity=gemma_similarity,
                    battery_similarity=battery_similarity,
                ),
                input_preview=_preview(input_text),
                target_preview=_preview(target_text),
                gemma_preview=_preview(gemma_reply),
                battery_preview=_preview(battery_reply),
            )
            example_results.append(result)
            per_dataset_results[dataset_name].append(result)

    dataset_summaries = {
        dataset_name: _summarize_results(values)
        for dataset_name, values in per_dataset_results.items()
        if values
    }
    overall_summary = _summarize_results(example_results)
    payload = {
        "pure_gemma_model": model_name,
        "battery_config": str(battery_config_path),
        "datasets_root": str(datasets_root),
        "max_examples_per_dataset": args.max_examples_per_dataset,
        "dataset_summaries": dataset_summaries,
        "overall_summary": overall_summary,
        "example_results": [asdict(item) for item in example_results],
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    output_md.write_text(
        _build_markdown_report(
            model_name=model_name,
            battery_config_path=battery_config_path,
            dataset_summaries=dataset_summaries,
            overall_summary=overall_summary,
            examples=example_results,
        ),
        "utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(output_json)
    print(output_md)


if __name__ == "__main__":
    main()
