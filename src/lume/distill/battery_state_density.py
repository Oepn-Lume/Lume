"""Builders for high-state-density battery supervision datasets."""

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


def _trim(text: str, limit: int = 240) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text("utf-8", errors="ignore").strip()


def _latest_assistant_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if str(message.get("role", "")).lower() == "assistant":
            return str(message.get("content", "")).strip()
    return ""


def _summarize_tool_trace(payload: dict[str, Any]) -> tuple[str, str]:
    tool_calls = payload.get("tool_calls", [])
    if not isinstance(tool_calls, list) or not tool_calls:
        return "n/a", "n/a"
    latest = tool_calls[-1] if isinstance(tool_calls[-1], dict) else {}
    latest_tool = str(latest.get("tool", "n/a"))
    latest_summary = str(latest.get("output_summary", "n/a"))
    return latest_tool, _trim(latest_summary, 160)


def _summarize_file_changes(payload: dict[str, Any]) -> tuple[str, str]:
    file_changes = payload.get("file_changes", [])
    if not isinstance(file_changes, list) or not file_changes:
        return "n/a", "n/a"
    latest = file_changes[-1] if isinstance(file_changes[-1], dict) else {}
    latest_path = str(latest.get("path", "n/a"))
    latest_summary = str(latest.get("summary", "n/a"))
    return latest_path, _trim(latest_summary, 160)


def _build_context_block(task_dir: Path, task_payload: dict[str, Any]) -> str:
    messages = _read_jsonl(task_dir / "conversation.jsonl")
    prompt_response = _read_json(task_dir / "prompt_response.json") if (task_dir / "prompt_response.json").exists() else {"pairs": []}
    tool_trace = _read_json(task_dir / "tool_trace.json") if (task_dir / "tool_trace.json").exists() else {"tool_calls": []}
    file_changes = _read_json(task_dir / "file_changes.json") if (task_dir / "file_changes.json").exists() else {"file_changes": []}
    outcome = _read_json(task_dir / "outcome.json") if (task_dir / "outcome.json").exists() else {}
    onsite_snapshot = _read_json(task_dir / "artifacts" / "onsite_snapshot.json") if (task_dir / "artifacts" / "onsite_snapshot.json").exists() else {}
    battery_dispatch = _read_json(task_dir / "artifacts" / "battery_dispatch.json") if (task_dir / "artifacts" / "battery_dispatch.json").exists() else {}
    hybrid_refinement = _read_json(task_dir / "artifacts" / "hybrid_refinement.json") if (task_dir / "artifacts" / "hybrid_refinement.json").exists() else {}

    latest_tool, latest_tool_summary = _summarize_tool_trace(tool_trace)
    latest_file, latest_file_summary = _summarize_file_changes(file_changes)
    pair_count = len(prompt_response.get("pairs", [])) if isinstance(prompt_response.get("pairs", []), list) else 0
    cascade = battery_dispatch.get("cascade_experts", [])
    if isinstance(cascade, list):
        cascade_text = " -> ".join(
            _trim(str(step.get("expert_name", "")), 40) if isinstance(step, dict) else _trim(str(step), 40)
            for step in cascade
        ) or "n/a"
    else:
        cascade_text = "n/a"

    context_lines = [
        f"Task_ID: {task_payload.get('task_id', task_dir.name)}",
        f"User_Goal: {_trim(str(task_payload.get('user_goal', '')), 180)}",
        f"Route_Mode: {task_payload.get('route_mode', 'n/a')}",
        f"Planning_Strategy: {task_payload.get('metadata', {}).get('planning_strategy', 'n/a') if isinstance(task_payload.get('metadata'), dict) else 'n/a'}",
        f"Output_Source: {task_payload.get('output_source', 'n/a')}",
        f"Result_Status: {task_payload.get('result_status', 'n/a')}",
        f"Value_Score: {task_payload.get('value_score', 'n/a')}",
        f"Message_Count: {task_payload.get('message_count', 0)}",
        f"Tool_Call_Count: {task_payload.get('tool_call_count', 0)}",
        f"File_Change_Count: {task_payload.get('file_change_count', 0)}",
        f"Prompt_Response_Count: {pair_count}",
        f"Latest_Tool: {latest_tool}",
        f"Latest_Tool_Result: {latest_tool_summary}",
        f"Latest_File: {latest_file}",
        f"Latest_File_Change: {latest_file_summary}",
        f"Last_Assistant: {_trim(_latest_assistant_message(messages), 180)}",
        f"Notes_Summary: {_trim(_read_optional_text(task_dir / 'notes.md'), 220)}",
        f"Diff_Summary: {_trim(_read_optional_text(task_dir / 'file_diff_summary.md'), 180)}",
        f"Outcome_Summary: {_trim(json.dumps(outcome, ensure_ascii=False), 180) if outcome else 'n/a'}",
        f"Onsite_Expanded_Task: {_trim(str(onsite_snapshot.get('expanded_task', 'n/a')), 180)}",
        f"Onsite_Working_Dir: {_trim(str(onsite_snapshot.get('working_dir', 'n/a')), 120)}",
        f"Battery_Primary_Expert: {_trim(str(battery_dispatch.get('primary_expert', 'n/a')), 80)}",
        f"Battery_Cascade: {_trim(cascade_text, 180)}",
        f"Hybrid_Local_Length: {hybrid_refinement.get('local_length', 'n/a') if isinstance(hybrid_refinement, dict) else 'n/a'}",
        f"Hybrid_Cloud_Length: {hybrid_refinement.get('cloud_length', 'n/a') if isinstance(hybrid_refinement, dict) else 'n/a'}",
    ]
    return "\n".join(context_lines)


def build_battery_state_dataset(
    task_runs_root: Path,
    datasets_root: Path,
    *,
    output_filename: str = "battery_state_sft.jsonl",
) -> Path:
    """Build a high-state-density battery dataset from task-run artifacts."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / output_filename
    records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        task_payload = _read_json(task_json)
        prompt_response = _read_json(task_dir / "prompt_response.json") if (task_dir / "prompt_response.json").exists() else {"pairs": []}
        context_block = _build_context_block(task_dir, task_payload)
        pairs = prompt_response.get("pairs", [])
        if not isinstance(pairs, list):
            pairs = []

        for index, pair in enumerate(pairs, start=1):
            prompt = str(pair.get("prompt", "")).strip()
            response = str(pair.get("response", "")).strip()
            if not prompt or not response:
                continue
            records.append(
                {
                    "task_id": f"{task_payload.get('task_id', task_dir.name)}-battery-state-{index}",
                    "input": "\n".join(
                        [
                            context_block,
                            "",
                            f"Active_Prompt: {_trim(prompt, 240)}",
                            "Task: produce the best local battery response using the full current worksite state.",
                        ]
                    ).strip(),
                    "target": response,
                    "metadata": {
                        "source": "battery_state_density",
                        "parent_task_id": task_payload.get("task_id", task_dir.name),
                        "route_mode": task_payload.get("route_mode"),
                        "result_status": task_payload.get("result_status"),
                        "value_score": task_payload.get("value_score", 0.0),
                        "has_onsite_snapshot": (task_dir / "artifacts" / "onsite_snapshot.json").exists(),
                        "has_battery_dispatch": (task_dir / "artifacts" / "battery_dispatch.json").exists(),
                        "has_hybrid_refinement": (task_dir / "artifacts" / "hybrid_refinement.json").exists(),
                        "has_diff_summary": (task_dir / "file_diff_summary.md").exists(),
                        "has_prompt_response": True,
                    },
                }
            )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
