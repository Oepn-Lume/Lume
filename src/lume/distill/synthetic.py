"""Utilities for merging generated synthetic corpora into trainable datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def merge_synthetic_corpus(generated_root: Path, datasets_root: Path) -> Path:
    """Copy accepted generated samples into the main training datasets directory."""
    source_path = generated_root / "generated_final" / "train.jsonl"
    output_path = datasets_root / "synthetic_sft.jsonl"
    datasets_root.mkdir(parents=True, exist_ok=True)

    records = []
    for record in _read_jsonl(source_path):
        records.append(
            {
                "task_id": record.get("task_id"),
                "input": record.get("input", ""),
                "target": record.get("target", ""),
                "metadata": {
                    "source": "synthetic_cloud_factory",
                    "category": record.get("category"),
                    "quality_score": record.get("quality_score"),
                    "teacher_model": record.get("teacher_model"),
                    "judge_model": record.get("judge_model"),
                },
            }
        )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
