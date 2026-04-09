"""Evaluate the locally trained local model on current datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.evaluation import evaluate_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v2-realcloud"),
    )
    parser.add_argument(
        "--dataset",
        default="",
    )
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument("--max-examples", type=int, default=24)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--output-json",
        default="",
    )
    parser.add_argument(
        "--output-md",
        default="",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _default_suite(datasets_root: Path) -> dict[str, Path]:
    return {
        "bootstrap": datasets_root / "real_cloud_bootstrap_sft.jsonl",
        "full_fidelity": datasets_root / "real_cloud_full_fidelity_sft.jsonl",
        "hybrid_refinement": datasets_root / "hybrid_refinement_sft.jsonl",
        "code_execution": datasets_root / "real_code_execution_sft.jsonl",
    }


def _build_markdown_report(
    model_root: Path,
    results: dict[str, dict[str, Any]],
    training_metrics: dict[str, Any] | None,
) -> str:
    lines = [
        f"# Local Model Evaluation Report",
        "",
        f"- Model Root: `{model_root}`",
    ]
    if training_metrics:
        lines.extend(
            [
                f"- Training Mode: `{training_metrics.get('training_mode', 'unknown')}`",
                f"- Final Loss: `{training_metrics.get('final_loss', 'n/a')}`",
                f"- Training Perplexity: `{training_metrics.get('perplexity', 'n/a')}`",
                f"- Device: `{training_metrics.get('device', 'n/a')}`",
                "",
            ]
        )
    else:
        lines.append("")

    lines.extend(
        [
            "## Dataset Results",
            "",
            "| Dataset | Examples | Avg Loss | Perplexity | Char Match | Prefix Match |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, payload in results.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    name,
                    str(payload.get("examples_evaluated", 0)),
                    str(payload.get("avg_loss", "n/a")),
                    str(payload.get("perplexity", "n/a")),
                    str(payload.get("avg_char_match", "n/a")),
                    str(payload.get("exact_prefix_match_rate", "n/a")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    model_root = Path(args.model_root)
    datasets_root = Path(args.datasets_root)
    if args.dataset:
        dataset_map = {Path(args.dataset).stem: Path(args.dataset)}
    else:
        dataset_map = {
            name: path for name, path in _default_suite(datasets_root).items() if path.exists()
        }

    results: dict[str, dict[str, Any]] = {}
    for name, dataset_path in dataset_map.items():
        results[name] = evaluate_model(
            model_root,
            dataset_path,
            max_examples=args.max_examples,
            device=args.device,
        )

    training_metrics_path = model_root / "metrics.json"
    training_metrics = _read_json(training_metrics_path) if training_metrics_path.exists() else None
    payload = {
        "model_root": str(model_root),
        "max_examples": args.max_examples,
        "device": args.device,
        "training_metrics": training_metrics,
        "results": results,
    }

    output_json = Path(args.output_json) if args.output_json else model_root / "evaluation_report.json"
    output_md = Path(args.output_md) if args.output_md else model_root / "evaluation_report.md"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    output_md.write_text(
        _build_markdown_report(model_root, results, training_metrics),
        "utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(output_json)
    print(output_md)


if __name__ == "__main__":
    main()
