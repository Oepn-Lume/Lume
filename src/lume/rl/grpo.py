"""Minimal group-relative preference optimization utilities for on-site alignment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .dpo import PreferenceTrainingConfig, train_preference_model


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


@dataclass(slots=True)
class GroupPreferenceTrainingConfig:
    dataset_path: str
    output_root: str
    model_name_or_path: str = "uer/gpt2-chinese-cluecorpussmall"
    epochs: int = 1
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 0.0
    warmup_ratio: float = 0.03
    gradient_accumulation_steps: int = 1
    max_length: int = 256
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    beta: float = 0.1
    max_samples: int | None = None
    seed: int = 42
    device: str = "auto"


def _convert_group_records(path: Path, *, max_samples: int | None = None) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for record in _read_jsonl(path):
        prompt = str(record.get("prompt", "")).strip()
        candidates = record.get("candidates", [])
        if not prompt or not isinstance(candidates, list) or len(candidates) < 2:
            continue
        sorted_candidates = sorted(
            [candidate for candidate in candidates if isinstance(candidate, dict)],
            key=lambda item: float(item.get("score", 0.0)),
            reverse=True,
        )
        if len(sorted_candidates) < 2:
            continue
        chosen = str(sorted_candidates[0].get("text", "")).strip()
        rejected = str(sorted_candidates[-1].get("text", "")).strip()
        if not chosen or not rejected or chosen == rejected:
            continue
        weight = max(
            0.5,
            float(sorted_candidates[0].get("score", 1.0)) - float(sorted_candidates[-1].get("score", 0.0)),
        )
        converted.append(
            {
                "task_id": str(record.get("task_id", "group-preference")),
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "weight": round(weight, 4),
                "metadata": {
                    **(record.get("metadata", {}) if isinstance(record.get("metadata", {}), dict) else {}),
                    "source": "group_relative_preference",
                    "group_candidate_count": len(sorted_candidates),
                    "preference_weight": round(weight, 4),
                },
            }
        )
        if max_samples is not None and len(converted) >= max_samples:
            break
    return converted


def train_group_preference_model(config: GroupPreferenceTrainingConfig) -> Path:
    dataset_path = Path(config.dataset_path)
    output_root = Path(config.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    converted_records = _convert_group_records(dataset_path, max_samples=config.max_samples)
    if not converted_records:
        raise RuntimeError("No valid group preference records found for GRPO training.")

    flattened_path = output_root / "grpo_flattened_pairs.jsonl"
    flattened_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in converted_records) + "\n",
        "utf-8",
    )

    dpo_config = PreferenceTrainingConfig(
        dataset_path=str(flattened_path),
        output_root=str(output_root),
        model_name_or_path=config.model_name_or_path,
        epochs=config.epochs,
        batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        warmup_ratio=config.warmup_ratio,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        max_length=config.max_length,
        lora_r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        beta=config.beta,
        max_samples=None,
        seed=config.seed,
        device=config.device,
    )
    result = train_preference_model(dpo_config)
    metrics_path = Path(result) / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text("utf-8"))
        metrics["training_mode"] = "transformers_peft_grpo_minimal"
        metrics["group_record_count"] = len(converted_records)
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", "utf-8")
    config_path = Path(result) / "training_config.json"
    if config_path.exists():
        payload = json.loads(config_path.read_text("utf-8"))
        payload["training_mode"] = "transformers_peft_grpo_minimal"
        payload["group_record_count"] = len(converted_records)
        config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return result
