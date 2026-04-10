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


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError:
        return None


def _discover_preference_training_metrics(distilled_root: Path) -> dict[str, Any]:
    candidates: list[tuple[str, Path]] = [
        ("onsite_dpo_weighted", distilled_root / "transformers-dpo-onsite-weighted-smoke" / "metrics.json"),
        ("onsite_grpo", distilled_root / "transformers-grpo-onsite-smoke" / "metrics.json"),
        ("onsite_dpo", distilled_root / "transformers-dpo-onsite-smoke" / "metrics.json"),
    ]
    metrics_map: dict[str, Any] = {}
    for key, path in candidates:
        payload = _read_json(path)
        if payload is not None:
            metrics_map[key] = payload
    return metrics_map


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
        "codex_action": datasets_root / "codex_action_eval.jsonl",
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
    codex_action_perplexity = evaluations.get("codex_action", {}).get("perplexity")
    distilled_root = datasets_root.parent / "distilled"
    preference_metrics = _discover_preference_training_metrics(distilled_root)

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

    onsite_dpo_margin = preference_metrics.get("onsite_dpo_weighted", {}).get("avg_preference_margin")
    if onsite_dpo_margin is None:
        onsite_dpo_margin = preference_metrics.get("onsite_dpo", {}).get("avg_preference_margin")
    onsite_grpo_margin = preference_metrics.get("onsite_grpo", {}).get("avg_preference_margin")

    onsite_alignment_components: list[float] = []
    for margin in [onsite_dpo_margin, onsite_grpo_margin]:
        if isinstance(margin, (int, float)):
            onsite_alignment_components.append(max(0.0, min(1.0, float(margin) / 0.25)))
    onsite_alignment_score = (
        round(sum(onsite_alignment_components) / len(onsite_alignment_components), 3)
        if onsite_alignment_components
        else 0.0
    )
    codex_action_readiness = round(
        min(
            1.0,
            (0.65 * quality_from_perplexity(codex_action_perplexity if isinstance(codex_action_perplexity, (int, float)) else None))
            + (0.35 * onsite_alignment_score),
        ),
        3,
    )
    adaptive_local_quality = round(
        min(1.0, weighted_quality + (0.20 * onsite_alignment_score)),
        3,
    )
    adaptive_local_threshold = round(max(0.45, 0.7 - (0.20 * onsite_alignment_score)), 3)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "battery_model_ready": bool(evaluations),
        "local_quality_score": round(weighted_quality, 3),
        "adaptive_local_quality_score": adaptive_local_quality,
        "adaptive_local_threshold": adaptive_local_threshold,
        "model_root": str(model_root),
        "max_examples": max_examples,
        "bootstrap_perplexity": bootstrap_perplexity,
        "full_fidelity_perplexity": full_fidelity_perplexity,
        "hybrid_refinement_perplexity": hybrid_refinement_perplexity,
        "codex_action_perplexity": codex_action_perplexity,
        "code_execution_perplexity": code_execution_perplexity,
        "onsite_dpo_margin": onsite_dpo_margin,
        "onsite_grpo_margin": onsite_grpo_margin,
        "onsite_alignment_score": onsite_alignment_score,
        "codex_action_readiness": codex_action_readiness,
        "preference_training_metrics": preference_metrics,
        "evaluations": evaluations,
        "notes": "Auto-generated routing quality snapshot based on local model evaluation plus on-site DPO/GRPO preference metrics.",
    }


def append_quality_history(snapshot: dict[str, Any], history_path: Path) -> Path:
    """Append a quality snapshot to a JSONL history file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return history_path
