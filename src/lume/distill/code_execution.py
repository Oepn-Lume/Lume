"""Builders for code- and execution-oriented training datasets."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".ps1",
    ".sql",
    ".html",
    ".css",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


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


def _extract_code_blocks(text: str) -> list[str]:
    blocks = re.findall(r"```[^\n`]*\n(.*?)```", text, flags=re.DOTALL)
    return [block.strip() for block in blocks if block.strip()]


def _is_real_codex_message(record: dict[str, Any]) -> bool:
    metadata = record.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("source") == "codex_session_import":
        return True
    source = str(record.get("source", ""))
    return source.startswith("codex_")


def _build_codeblock_records(raw_logs_root: Path) -> list[dict[str, Any]]:
    import_path = raw_logs_root / "codex-session-import.jsonl"
    records = _read_jsonl(import_path)
    built: list[dict[str, Any]] = []
    for index in range(len(records) - 1):
        current_record = records[index]
        next_record = records[index + 1]
        if current_record.get("role") != "user":
            continue
        if next_record.get("role") != "assistant":
            continue
        if not _is_real_codex_message(current_record) or not _is_real_codex_message(next_record):
            continue
        if current_record.get("session_file") != next_record.get("session_file"):
            continue
        assistant_text = str(next_record.get("content", "")).strip()
        if not assistant_text or assistant_text.startswith("<"):
            continue
        code_blocks = _extract_code_blocks(assistant_text)
        if not code_blocks:
            continue
        built.append(
            {
                "task_id": f"real-codeblock-{index}",
                "input": str(current_record.get("content", "")).strip(),
                "target": "\n\n".join(code_blocks),
                "metadata": {
                    "source": "real_codex_codeblock",
                    "session_file": next_record.get("session_file"),
                    "timestamp": next_record.get("timestamp"),
                    "code_block_count": len(code_blocks),
                },
            }
        )
    return built


def _build_function_call_records(raw_logs_root: Path) -> list[dict[str, Any]]:
    import_path = raw_logs_root / "codex-session-import.jsonl"
    records = _read_jsonl(import_path)
    pending_calls: dict[tuple[str, str], dict[str, Any]] = {}
    built: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        source = str(record.get("source", ""))
        raw_payload = record.get("raw_payload", {})
        session_file = str(record.get("session_file", ""))
        if not isinstance(raw_payload, dict):
            continue

        if source == "codex_response_item:function_call":
            call_id = str(raw_payload.get("call_id", "")).strip()
            tool_name = str(raw_payload.get("name", "")).strip()
            if not call_id or not tool_name:
                continue
            arguments_text = str(raw_payload.get("arguments", "")).strip()
            pending_calls[(session_file, call_id)] = {
                "tool_name": tool_name,
                "arguments_text": arguments_text,
                "timestamp": record.get("timestamp"),
            }
            continue

        if source != "codex_response_item:function_call_output":
            continue
        call_id = str(raw_payload.get("call_id", "")).strip()
        if not call_id:
            continue
        pending = pending_calls.get((session_file, call_id))
        if pending is None:
            continue

        arguments_payload = _safe_json_loads(pending["arguments_text"]) or {}
        output_text = str(raw_payload.get("output", "")).strip()
        if not output_text:
            continue

        input_lines = [
            f"Tool: {pending['tool_name']}",
            f"Session: {session_file}",
        ]
        if arguments_payload:
            command = str(arguments_payload.get("command", "")).strip()
            if command:
                input_lines.append(f"Command: {command}")
            workdir = str(arguments_payload.get("workdir", "")).strip()
            if workdir:
                input_lines.append(f"Workdir: {workdir}")
        elif pending["arguments_text"]:
            input_lines.append(f"Arguments: {pending['arguments_text']}")

        built.append(
            {
                "task_id": f"real-function-call-{index}",
                "input": "\n".join(input_lines),
                "target": output_text,
                "metadata": {
                    "source": "real_function_call_output",
                    "session_file": session_file,
                    "tool_name": pending["tool_name"],
                    "timestamp": record.get("timestamp"),
                    "call_id": call_id,
                },
            }
        )
    return built


def _resolve_artifact_path(lume_root: Path, relative_path: str) -> Path | None:
    if not relative_path:
        return None
    candidate = lume_root / relative_path
    if candidate.exists():
        return candidate
    return None


def _build_task_run_code_records(task_runs_root: Path) -> list[dict[str, Any]]:
    lume_root = task_runs_root.parents[1]
    built: list[dict[str, Any]] = []
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        file_changes_json = task_dir / "file_changes.json"
        if not task_json.exists() or not file_changes_json.exists():
            continue
        task_payload = _read_json(task_json)
        file_changes_payload = _read_json(file_changes_json)
        tool_trace = _read_json(task_dir / "tool_trace.json") if (task_dir / "tool_trace.json").exists() else {}
        tool_calls = tool_trace.get("tool_calls", [])

        for index, file_change in enumerate(file_changes_payload.get("file_changes", [])):
            relative_path = str(file_change.get("path", "")).strip()
            resolved_path = _resolve_artifact_path(lume_root, relative_path)
            if resolved_path is None:
                continue
            if resolved_path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            try:
                file_content = resolved_path.read_text("utf-8")
            except UnicodeDecodeError:
                continue
            if not file_content.strip():
                continue
            summary = str(file_change.get("summary", "")).strip()
            tool_names = [
                str(tool_call.get("tool") or tool_call.get("name") or "").strip()
                for tool_call in tool_calls
                if isinstance(tool_call, dict)
            ]
            tool_names = [name for name in tool_names if name]
            input_lines = [
                f"User goal: {task_payload.get('user_goal', '')}".strip(),
                f"Changed file: {relative_path}",
            ]
            if summary:
                input_lines.append(f"Change summary: {summary}")
            if tool_names:
                input_lines.append(f"Tools: {', '.join(tool_names)}")
            built.append(
                {
                    "task_id": f"{task_payload.get('task_id', task_dir.name)}-file-{index}",
                    "input": "\n".join(line for line in input_lines if line),
                    "target": file_content,
                    "metadata": {
                        "source": "real_task_run_file",
                        "task_id": task_payload.get("task_id", task_dir.name),
                        "relative_path": relative_path,
                        "change_type": file_change.get("change_type"),
                        "route_mode": task_payload.get("route_mode"),
                        "value_score": task_payload.get("value_score", 0.0),
                    },
                }
            )
    return built


def build_real_code_execution_dataset(
    task_runs_root: Path,
    raw_logs_root: Path,
    datasets_root: Path,
) -> Path:
    """Build a real code/execution SFT dataset from task artifacts and codex sessions."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "real_code_execution_sft.jsonl"
    records = _build_task_run_code_records(task_runs_root)
    records.extend(_build_codeblock_records(raw_logs_root))
    records.extend(_build_function_call_records(raw_logs_root))
    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
