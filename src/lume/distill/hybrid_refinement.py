"""Builders for hybrid local-draft versus cloud-refinement training datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _build_record(
    *,
    task_id: str,
    route_mode: str,
    value_score: float,
    user_goal: str,
    local_draft: str,
    cloud_refinement: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    input_lines = [
        f"User goal: {user_goal}",
        "",
        "Local Battery Model draft:",
        local_draft,
        "",
        "Task: refine the local draft into the higher-confidence planning output.",
    ]
    return {
        "task_id": f"{task_id}-hybrid-refinement",
        "input": "\n".join(input_lines).strip(),
        "target": cloud_refinement,
        "metadata": {
            "source": metadata.get("source", "hybrid_refinement_artifact"),
            "task_id": task_id,
            "route_mode": route_mode,
            "value_score": value_score,
            **metadata,
        },
    }


def build_hybrid_refinement_dataset(task_runs_root: Path, datasets_root: Path) -> Path:
    """Build a dataset from structured hybrid planning refinement artifacts."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "hybrid_refinement_sft.jsonl"
    records: list[dict[str, Any]] = []

    seen_task_ids: set[str] = set()

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

        current_task_id = str(task_payload.get("task_id", task_dir.name))
        records.append(
            _build_record(
                task_id=current_task_id,
                route_mode=str(task_payload.get("route_mode", "")),
                value_score=float(task_payload.get("value_score", 0.0)),
                user_goal=user_goal,
                local_draft=local_draft,
                cloud_refinement=cloud_refinement,
                metadata={
                    "source": "hybrid_refinement_artifact",
                    "local_model": artifact_payload.get("local_model"),
                    "cloud_model": artifact_payload.get("cloud_model"),
                    "local_length": artifact_payload.get("local_length"),
                    "cloud_length": artifact_payload.get("cloud_length"),
                    "similarity_score": artifact_payload.get("metadata", {}).get("similarity_score"),
                    "local_quality_score": artifact_payload.get("metadata", {}).get("local_quality_score"),
                },
            )
        )
        seen_task_ids.add(current_task_id)

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        conversation_path = task_dir / "conversation.jsonl"
        if not task_json.exists() or not conversation_path.exists():
            continue
        task_payload = _read_json(task_json)
        current_task_id = str(task_payload.get("task_id", task_dir.name))
        if current_task_id in seen_task_ids:
            continue
        if str(task_payload.get("route_mode", "")).strip() != "hybrid":
            continue

        user_goal = str(task_payload.get("user_goal", "")).strip()
        if not user_goal:
            continue
        local_draft = ""
        cloud_refinement = ""
        local_model = None
        cloud_model = None
        similarity_score = None
        local_quality_score = None

        for record in _read_jsonl(conversation_path):
            if str(record.get("role", "")) != "assistant":
                continue
            if str(record.get("source", "")) != "cloud":
                continue
            message_type = str(record.get("message_type", "")).strip()
            metadata = record.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            if message_type == "local_reasoning" and not local_draft:
                local_draft = str(record.get("content", "")).strip()
                local_model = record.get("model")
                similarity_score = metadata.get("similarity_score", similarity_score)
                local_quality_score = metadata.get("local_quality_score", local_quality_score)
            elif message_type == "reasoning" and metadata.get("hybrid") and not cloud_refinement:
                cloud_refinement = str(record.get("content", "")).strip()
                cloud_model = record.get("model")

        if not local_draft or not cloud_refinement:
            continue

        records.append(
            _build_record(
                task_id=current_task_id,
                route_mode=str(task_payload.get("route_mode", "")),
                value_score=float(task_payload.get("value_score", 0.0)),
                user_goal=user_goal,
                local_draft=local_draft,
                cloud_refinement=cloud_refinement,
                metadata={
                    "source": "hybrid_refinement_conversation",
                    "local_model": local_model,
                    "cloud_model": cloud_model,
                    "local_length": len(local_draft),
                    "cloud_length": len(cloud_refinement),
                    "similarity_score": similarity_score,
                    "local_quality_score": local_quality_score,
                },
            )
        )
        seen_task_ids.add(current_task_id)

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
