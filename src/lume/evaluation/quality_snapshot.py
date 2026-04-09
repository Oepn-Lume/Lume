"""Helpers for building routing-ready local quality snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .local_model import evaluate_model


def quality_from_perplexity(perplexity: float | None) -> float:
    """Map perplexity into a bounded 0-1 routing quality score."""
    if perplexity is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 / (1.0 + (perplexity / 3.0))))


def build_quality_snapshot(
    model_root: Path,
    datasets_root: Path,
    *,
    max_examples: int = 8,
    device: str = "auto",
) -> dict[str, Any]:
    """Evaluate the local model and build a routing quality snapshot payload."""
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
            max_examples=max_examples,
            device=device,
        )

    bootstrap_perplexity = evaluations.get("bootstrap", {}).get("perplexity")
    full_fidelity_perplexity = evaluations.get("full_fidelity", {}).get("perplexity")
    code_execution_perplexity = evaluations.get("code_execution", {}).get("perplexity")
    hybrid_refinement_perplexity = evaluations.get("hybrid_refinement", {}).get("perplexity")

    quality_components = [
        (0.35, quality_from_perplexity(bootstrap_perplexity if isinstance(bootstrap_perplexity, (int, float)) else None)),
        (0.30, quality_from_perplexity(full_fidelity_perplexity if isinstance(full_fidelity_perplexity, (int, float)) else None)),
        (0.20, quality_from_perplexity(hybrid_refinement_perplexity if isinstance(hybrid_refinement_perplexity, (int, float)) else None)),
        (0.15, quality_from_perplexity(code_execution_perplexity if isinstance(code_execution_perplexity, (int, float)) else None)),
    ]
    total_weight = sum(weight for weight, _score in quality_components)
    weighted_quality = (
        sum(weight * score for weight, score in quality_components) / total_weight
        if total_weight
        else 0.0
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "battery_model_ready": bool(evaluations),
        "local_quality_score": round(weighted_quality, 3),
        "model_root": str(model_root),
        "max_examples": max_examples,
        "bootstrap_perplexity": bootstrap_perplexity,
        "full_fidelity_perplexity": full_fidelity_perplexity,
        "hybrid_refinement_perplexity": hybrid_refinement_perplexity,
        "code_execution_perplexity": code_execution_perplexity,
        "evaluations": evaluations,
        "notes": "Auto-generated routing quality snapshot based on local model evaluation across bootstrap, full-fidelity, hybrid-refinement, and code-execution datasets.",
    }


def append_quality_history(snapshot: dict[str, Any], history_path: Path) -> Path:
    """Append a quality snapshot to a JSONL history file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return history_path
