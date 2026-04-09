"""Build reinforcement-learning style datasets from real task outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _jsonl_write(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )


def _build_reward_records(task_runs_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        outcome_json = task_dir / "outcome.json"
        tool_trace_json = task_dir / "tool_trace.json"
        if not task_json.exists() or not outcome_json.exists():
            continue

        task_payload = _read_json(task_json)
        outcome_payload = _read_json(outcome_json)
        tool_payload = _read_json(tool_trace_json) if tool_trace_json.exists() else {"tool_calls": []}
        tool_calls = tool_payload.get("tool_calls", [])
        completed = 1.0 if outcome_payload.get("result_status") == "completed" else 0.0
        value_score = float(outcome_payload.get("value_score", 0.0))
        file_change_count = int(task_payload.get("file_change_count", 0))
        tool_call_count = int(task_payload.get("tool_call_count", 0))

        # Minimal real-world execution feedback signal.
        reward = round(
            (0.55 * value_score)
            + (0.25 * completed)
            + (0.10 if file_change_count > 0 else 0.0)
            + (0.10 if tool_call_count > 0 else 0.0),
            4,
        )
        records.append(
            {
                "task_id": task_payload.get("task_id", task_dir.name),
                "input": task_payload.get("user_goal", ""),
                "target": {
                    "result_status": outcome_payload.get("result_status"),
                    "tool_calls": tool_calls,
                    "file_change_count": file_change_count,
                },
                "reward": reward,
                "metadata": {
                    "source": "real_execution_feedback",
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": value_score,
                    "completed": bool(completed),
                    "tool_call_count": tool_call_count,
                    "file_change_count": file_change_count,
                },
            }
        )
        for tool_index, tool_call in enumerate(tool_calls):
            if not isinstance(tool_call, dict):
                continue
            tool_name = str(tool_call.get("tool") or tool_call.get("name") or "").strip()
            if not tool_name:
                continue
            tool_status = str(tool_call.get("status", "completed")).strip()
            tool_reward = round(
                (0.5 if tool_status == "completed" else 0.0)
                + (0.25 * value_score)
                + (0.15 if str(tool_call.get("output_summary", "")).strip() else 0.0)
                + (0.10 if file_change_count > 0 else 0.0),
                4,
            )
            records.append(
                {
                    "task_id": f"{task_payload.get('task_id', task_dir.name)}-tool-{tool_index}",
                    "input": f"User goal: {task_payload.get('user_goal', '')}\nTool: {tool_name}",
                    "target": {
                        "status": tool_status,
                        "output_summary": tool_call.get("output_summary", ""),
                        "arguments": tool_call.get("arguments", {}),
                    },
                    "reward": tool_reward,
                    "metadata": {
                        "source": "real_execution_feedback_tool",
                        "route_mode": task_payload.get("route_mode"),
                        "value_score": value_score,
                        "completed": tool_status == "completed",
                        "tool_name": tool_name,
                        "tool_call_count": tool_call_count,
                        "file_change_count": file_change_count,
                    },
                }
            )
    return records


def _build_preference_records(task_runs_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_task_ids: set[str] = set()
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        artifact_json = task_dir / "artifacts" / "hybrid_refinement.json"
        if not task_json.exists() or not artifact_json.exists():
            continue

        task_payload = _read_json(task_json)
        artifact_payload = _read_json(artifact_json)
        user_goal = str(task_payload.get("user_goal", "")).strip()
        local_draft = str(artifact_payload.get("local_draft", "")).strip()
        cloud_refinement = str(artifact_payload.get("cloud_refinement", "")).strip()
        if not user_goal or not local_draft or not cloud_refinement:
            continue

        prompt = "\n".join(
            [
                f"User goal: {user_goal}",
                "Select the better planning response for the task.",
            ]
        )
        records.append(
            {
                "task_id": f"{task_payload.get('task_id', task_dir.name)}-preference",
                "prompt": prompt,
                "chosen": cloud_refinement,
                "rejected": local_draft,
                "metadata": {
                    "source": "hybrid_refinement_preference",
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
        seen_task_ids.add(str(task_payload.get("task_id", task_dir.name)))

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        conversation_jsonl = task_dir / "conversation.jsonl"
        if not task_json.exists() or not conversation_jsonl.exists():
            continue
        task_payload = _read_json(task_json)
        task_id = str(task_payload.get("task_id", task_dir.name))
        if task_id in seen_task_ids:
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
        for line in conversation_jsonl.read_text("utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(record.get("role", "")) != "assistant":
                continue
            if str(record.get("source", "")) != "cloud":
                continue
            metadata = record.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            if str(record.get("message_type", "")).strip() == "local_reasoning" and not local_draft:
                local_draft = str(record.get("content", "")).strip()
                local_model = record.get("model")
            elif str(record.get("message_type", "")).strip() == "reasoning" and metadata.get("hybrid") and not cloud_refinement:
                cloud_refinement = str(record.get("content", "")).strip()
                cloud_model = record.get("model")

        if not local_draft or not cloud_refinement:
            continue

        prompt = "\n".join(
            [
                f"User goal: {user_goal}",
                "Select the better planning response for the task.",
            ]
        )
        records.append(
            {
                "task_id": f"{task_id}-preference",
                "prompt": prompt,
                "chosen": cloud_refinement,
                "rejected": local_draft,
                "metadata": {
                    "source": "hybrid_refinement_preference_conversation",
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "local_model": local_model,
                    "cloud_model": cloud_model,
                    "local_length": len(local_draft),
                    "cloud_length": len(cloud_refinement),
                },
            }
        )
        seen_task_ids.add(task_id)
    return records


def build_rlef_datasets(task_runs_root: Path, datasets_root: Path) -> list[Path]:
    """Build minimal RLEF/reward datasets from real task outcomes."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    reward_path = datasets_root / "rlef_reward.jsonl"
    preference_path = datasets_root / "rlef_preference.jsonl"

    reward_records = _build_reward_records(task_runs_root)
    preference_records = _build_preference_records(task_runs_root)

    _jsonl_write(reward_path, reward_records)
    _jsonl_write(preference_path, preference_records)
    return [reward_path, preference_path]
