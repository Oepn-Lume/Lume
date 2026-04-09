"""Builders for hybrid local-draft versus cloud-refinement training datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def build_hybrid_refinement_dataset(task_runs_root: Path, datasets_root: Path) -> Path:
    """Build a dataset from structured hybrid planning refinement artifacts."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "hybrid_refinement_sft.jsonl"
    records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        artifact_path = task_dir / "artifacts" / "hybrid_refinement.json"
        if not task_json.exists() or not artifact_path.exists():
            continue

        task_payload = _read_json(task_json)
        artifact_payload = _read_json(artifact_path)
        user_goal = str(task_payload.get("user_goal", "")).strip()
        local_draft = str(artifact_payload.get("local_draft", "")).strip()
        cloud_refinement = str(artifact_payload.get("cloud_refinement", "")).strip()
        if not user_goal or not local_draft or not cloud_refinement:
            continue

        input_lines = [
            f"User goal: {user_goal}",
            "",
            "Local Battery Model draft:",
            local_draft,
            "",
            "Task: refine the local draft into the higher-confidence planning output.",
        ]
        records.append(
            {
                "task_id": f"{task_payload.get('task_id', task_dir.name)}-hybrid-refinement",
                "input": "\n".join(input_lines).strip(),
                "target": cloud_refinement,
                "metadata": {
                    "source": "hybrid_refinement_artifact",
                    "task_id": task_payload.get("task_id", task_dir.name),
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "local_model": artifact_payload.get("local_model"),
                    "cloud_model": artifact_payload.get("cloud_model"),
                    "local_length": artifact_payload.get("local_length"),
                    "cloud_length": artifact_payload.get("cloud_length"),
                    "similarity_score": artifact_payload.get("metadata", {}).get("similarity_score"),
                    "local_quality_score": artifact_payload.get("metadata", {}).get("local_quality_score"),
                },
            }
        )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
