"""Build a routing-ready local quality snapshot from evaluation runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

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
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "configs" / "local_quality.json"),
    )
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def _quality_from_perplexity(perplexity: float | None) -> float:
    if perplexity is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 / (1.0 + (perplexity / 3.0))))


def main() -> None:
    args = parse_args()
    model_root = Path(args.model_root)
    datasets_root = Path(args.datasets_root)

    dataset_map = {
        "bootstrap": datasets_root / "real_cloud_bootstrap_sft.jsonl",
        "full_fidelity": datasets_root / "real_cloud_full_fidelity_sft.jsonl",
        "code_execution": datasets_root / "real_code_execution_sft.jsonl",
        "hybrid_refinement": datasets_root / "hybrid_refinement_sft.jsonl",
    }
    evaluations: dict[str, dict[str, object]] = {}
    for name, path in dataset_map.items():
        if not path.exists():
            continue
        evaluations[name] = evaluate_model(
            model_root,
            path,
            max_examples=args.max_examples,
            device=args.device,
        )

    bootstrap_perplexity = evaluations.get("bootstrap", {}).get("perplexity")
    full_fidelity_perplexity = evaluations.get("full_fidelity", {}).get("perplexity")
    code_execution_perplexity = evaluations.get("code_execution", {}).get("perplexity")
    hybrid_refinement_perplexity = evaluations.get("hybrid_refinement", {}).get("perplexity")

    quality_components = [
        (0.35, _quality_from_perplexity(bootstrap_perplexity if isinstance(bootstrap_perplexity, (int, float)) else None)),
        (0.30, _quality_from_perplexity(full_fidelity_perplexity if isinstance(full_fidelity_perplexity, (int, float)) else None)),
        (0.20, _quality_from_perplexity(hybrid_refinement_perplexity if isinstance(hybrid_refinement_perplexity, (int, float)) else None)),
        (0.15, _quality_from_perplexity(code_execution_perplexity if isinstance(code_execution_perplexity, (int, float)) else None)),
    ]
    total_weight = sum(weight for weight, _score in quality_components)
    weighted_quality = sum(weight * score for weight, score in quality_components) / total_weight if total_weight else 0.0

    payload = {
        "battery_model_ready": bool(evaluations),
        "local_quality_score": round(weighted_quality, 3),
        "model_root": str(model_root),
        "max_examples": args.max_examples,
        "bootstrap_perplexity": bootstrap_perplexity,
        "full_fidelity_perplexity": full_fidelity_perplexity,
        "hybrid_refinement_perplexity": hybrid_refinement_perplexity,
        "code_execution_perplexity": code_execution_perplexity,
        "evaluations": evaluations,
        "notes": "Auto-generated routing quality snapshot based on local model evaluation across bootstrap, full-fidelity, hybrid-refinement, and code-execution datasets.",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
