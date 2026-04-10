"""Dataset builders for distillation and memory supervision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .battery_cascade import build_battery_cascade_dataset
from .code_execution import build_real_code_execution_dataset
from .historical_backfill import build_historical_workspace_dataset
from .hybrid_refinement import build_hybrid_refinement_dataset
from .raw_dialogue import build_raw_dialogue_dataset

def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text("utf-8").splitlines()
        if line.strip()
    ]


def build_distill_datasets(
    task_runs_root: Path,
    datasets_root: Path,
    raw_logs_root: Path | None = None,
) -> list[Path]:
    """Generate simple SFT datasets from task runs."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    reasoning_records: list[dict[str, Any]] = []
    execution_records: list[dict[str, Any]] = []
    memory_records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue

        task_payload = _read_json(task_json)
        prompt_response = (
            _read_json(task_dir / "prompt_response.json")
            if (task_dir / "prompt_response.json").exists()
            else {"pairs": []}
        )
        tool_trace = (
            _read_json(task_dir / "tool_trace.json")
            if (task_dir / "tool_trace.json").exists()
            else {"tool_calls": []}
        )
        messages = _read_jsonl(task_dir / "conversation.jsonl")
        notes = (task_dir / "notes.md").read_text("utf-8").strip() if (task_dir / "notes.md").exists() else ""

        for pair in prompt_response.get("pairs", []):
            reasoning_records.append(
                {
                    "task_id": task_payload["task_id"],
                    "input": pair.get("prompt", ""),
                    "target": pair.get("response", ""),
                    "metadata": {
                        "route_mode": task_payload.get("route_mode"),
                        "value_score": task_payload.get("value_score", 0.0),
                        "source": "shadow_prompt_response",
                    },
                }
            )

        execution_records.append(
            {
                "task_id": task_payload["task_id"],
                "input": task_payload.get("user_goal", ""),
                "target": {
                    "tool_calls": tool_trace.get("tool_calls", []),
                    "message_count": task_payload.get("message_count", len(messages)),
                    "file_changes": task_payload.get("file_change_count", 0),
                },
                "metadata": {
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "source": "shadow_execution_trace",
                },
            }
        )

        memory_records.append(
            {
                "task_id": task_payload["task_id"],
                "input": task_payload.get("user_goal", ""),
                "target": notes,
                "metadata": {
                    "result_status": task_payload.get("result_status"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "source": "shadow_notes",
                },
            }
        )

    written: list[Path] = []
    output_map = {
        "sft_reasoning.jsonl": reasoning_records,
        "sft_execution.jsonl": execution_records,
        "memory_update.jsonl": memory_records,
    }
    for filename, records in output_map.items():
        path = datasets_root / filename
        lines = [json.dumps(record, ensure_ascii=False) for record in records]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), "utf-8")
        written.append(path)

    if raw_logs_root is not None:
        written.append(build_raw_dialogue_dataset(raw_logs_root, datasets_root))
        written.append(build_real_code_execution_dataset(task_runs_root, raw_logs_root, datasets_root))
    written.append(build_battery_cascade_dataset(task_runs_root, datasets_root))
    written.append(build_hybrid_refinement_dataset(task_runs_root, datasets_root))
    written.append(build_historical_workspace_dataset(task_runs_root.parent.parent, datasets_root))
    return written
