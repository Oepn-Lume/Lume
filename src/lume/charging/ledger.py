"""Append-only ledger builders for shadow charging assets."""

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
    for raw_line in path.read_text("utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), "utf-8")


def build_shadow_charge_ledger(task_runs_root: Path, output_root: Path) -> list[Path]:
    """Build an append-only shadow charging ledger from task runs."""

    output_root.mkdir(parents=True, exist_ok=True)
    ledger_path = output_root / "shadow_charge_ledger.jsonl"
    summary_path = output_root / "shadow_charge_summary.json"

    existing_records = _read_jsonl(ledger_path)
    existing_ids = {str(record.get("task_id")) for record in existing_records}
    new_records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        task_payload = _read_json(task_json)
        task_id = str(task_payload.get("task_id", "")).strip()
        if not task_id or task_id in existing_ids:
            continue
        tool_trace = _read_json(task_dir / "tool_trace.json") if (task_dir / "tool_trace.json").exists() else {}
        file_changes = _read_json(task_dir / "file_changes.json") if (task_dir / "file_changes.json").exists() else {}
        outcome = _read_json(task_dir / "outcome.json") if (task_dir / "outcome.json").exists() else {}
        manifest = _read_json(task_dir / "manifest.json") if (task_dir / "manifest.json").exists() else {}
        record = {
            "task_id": task_id,
            "timestamp": task_payload.get("timestamp"),
            "user_goal": task_payload.get("user_goal", ""),
            "route_mode": task_payload.get("route_mode"),
            "model_used": task_payload.get("model_used"),
            "result_status": task_payload.get("result_status"),
            "value_score": task_payload.get("value_score", 0.0),
            "output_source": task_payload.get("output_source"),
            "message_count": task_payload.get("message_count", 0),
            "tool_call_count": task_payload.get("tool_call_count", 0),
            "file_change_count": task_payload.get("file_change_count", 0),
            "files_changed": [
                change.get("path")
                for change in file_changes.get("file_changes", [])
                if isinstance(change, dict) and change.get("path")
            ],
            "tool_names": [
                call.get("tool")
                for call in tool_trace.get("tool_calls", [])
                if isinstance(call, dict) and call.get("tool")
            ],
            "outcome": outcome,
            "artifact_manifest": manifest.get("artifacts", {}),
            "task_dir": str(task_dir),
        }
        new_records.append(record)

    all_records = existing_records + new_records
    _write_jsonl(ledger_path, all_records)

    summary = {
        "record_count": len(all_records),
        "new_record_count": len(new_records),
        "completed_count": sum(1 for record in all_records if record.get("result_status") == "completed"),
        "high_value_count": sum(
            1 for record in all_records if float(record.get("value_score", 0.0) or 0.0) >= 0.9
        ),
        "local_route_count": sum(1 for record in all_records if record.get("route_mode") == "local"),
        "hybrid_route_count": sum(1 for record in all_records if record.get("route_mode") == "hybrid"),
        "cloud_route_count": sum(1 for record in all_records if record.get("route_mode") == "cloud"),
        "output_root": str(output_root),
        "ledger_path": str(ledger_path),
    }
    _write_json(summary_path, summary)
    return [ledger_path, summary_path]
