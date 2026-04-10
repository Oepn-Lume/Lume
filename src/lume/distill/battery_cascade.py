"""Builders for battery expert cascade supervision datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def build_battery_cascade_dataset(task_runs_root: Path, datasets_root: Path) -> Path:
    """Build a dataset from structured battery cascade artifacts."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "battery_cascade_sft.jsonl"
    records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        artifact_path = task_dir / "artifacts" / "battery_dispatch.json"
        if not task_json.exists() or not artifact_path.exists():
            continue

        task_payload = _read_json(task_json)
        artifact_payload = _read_json(artifact_path)
        cascade_outputs = artifact_payload.get("cascade_outputs", [])
        if not isinstance(cascade_outputs, list) or len(cascade_outputs) < 2:
            continue

        user_goal = str(task_payload.get("user_goal", "")).strip()
        route_mode = str(task_payload.get("route_mode", "")).strip()
        value_score = float(task_payload.get("value_score", 0.0))
        task_id = str(task_payload.get("task_id", task_dir.name))
        selected_expert_count = int(artifact_payload.get("selected_expert_count", len(cascade_outputs)))
        candidate_scores = artifact_payload.get("candidate_scores", {})
        if not user_goal:
            continue

        running_draft = ""
        for index, step in enumerate(cascade_outputs):
            if not isinstance(step, dict):
                continue
            output_text = str(step.get("output", "")).strip()
            expert_name = str(step.get("expert_name", "")).strip()
            domain = str(step.get("domain", "")).strip()
            if not output_text or not expert_name:
                continue

            if index == 0:
                input_text = "\n".join(
                    [
                        f"User goal: {user_goal}",
                        f"Route mode: {route_mode}",
                        f"Primary expert: {expert_name}",
                        f"Expert domain: {domain}",
                        "",
                        "Task: produce the first local battery draft for this task.",
                    ]
                ).strip()
            else:
                previous_step = cascade_outputs[index - 1]
                previous_expert = str(previous_step.get("expert_name", "")).strip()
                previous_output = str(previous_step.get("output", "")).strip()
                input_text = "\n".join(
                    [
                        f"User goal: {user_goal}",
                        f"Route mode: {route_mode}",
                        f"Previous expert: {previous_expert}",
                        f"Current expert: {expert_name}",
                        f"Current domain: {domain}",
                        "",
                        "Previous local draft:",
                        previous_output,
                        "",
                        "Task: refine or extend the previous draft from the current expert perspective.",
                    ]
                ).strip()

            records.append(
                {
                    "task_id": f"{task_id}-battery-cascade-step-{index + 1}",
                    "input": input_text,
                    "target": output_text,
                    "metadata": {
                        "source": "battery_dispatch_artifact",
                        "parent_task_id": task_id,
                        "route_mode": route_mode,
                        "value_score": value_score,
                        "selected_expert_count": selected_expert_count,
                        "primary_expert": artifact_payload.get("primary_expert"),
                        "expert_name": expert_name,
                        "expert_domain": domain,
                        "step": index + 1,
                        "matched_keywords": step.get("matched_keywords", []),
                        "candidate_scores": candidate_scores,
                    },
                }
            )
            running_draft = output_text or running_draft

        if running_draft and len(cascade_outputs) >= 2:
            records.append(
                {
                    "task_id": f"{task_id}-battery-cascade-final",
                    "input": "\n".join(
                        [
                            f"User goal: {user_goal}",
                            f"Route mode: {route_mode}",
                            f"Primary expert: {artifact_payload.get('primary_expert', '')}",
                            f"Selected expert count: {selected_expert_count}",
                            "",
                            "Expert cascade:",
                            " -> ".join(
                                str(step.get("expert_name", "")).strip()
                                for step in cascade_outputs
                                if isinstance(step, dict)
                            ),
                            "",
                            "Task: produce the final local battery result after multi-expert refinement.",
                        ]
                    ).strip(),
                    "target": running_draft,
                    "metadata": {
                        "source": "battery_dispatch_artifact_final",
                        "parent_task_id": task_id,
                        "route_mode": route_mode,
                        "value_score": value_score,
                        "selected_expert_count": selected_expert_count,
                        "primary_expert": artifact_payload.get("primary_expert"),
                        "candidate_scores": candidate_scores,
                    },
                }
            )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
