"""Dynamic context injection for improving Gemma's on-site awareness."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from lume.logging.codex_sessions import discover_session_files, normalize_session_event


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_ARCHIVED_ROOT = Path.home() / ".codex" / "archived_sessions"


@dataclass(slots=True)
class DynamicSnapshot:
    working_dir: str
    last_cmd: str
    pending_task: str
    current_focus: str
    recent_reasoning: str
    recent_patch: str
    recent_task_id: str
    recent_file: str
    expanded_task: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _trim(text: str, limit: int = 180) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _infer_working_dir(task: str) -> str:
    lowered = task.lower()
    if any(token in lowered for token in ["readme", "docs", "blog", "wiki"]):
        return "/docs/"
    if any(token in lowered for token in ["test", "bug", "patch", "python", "code", "script"]):
        return "/src/"
    if any(token in lowered for token in ["train", "dataset", "distill", "lora"]):
        return "/data/"
    return "/"


def _latest_task_snapshot(task_runs_root: Path) -> tuple[str, str, str, str]:
    task_dirs = [path for path in task_runs_root.iterdir() if path.is_dir()]
    if not task_dirs:
        return "", "", "", ""
    latest = max(task_dirs, key=lambda path: path.stat().st_mtime)
    task_id = latest.name
    pending_task = ""
    recent_file = ""
    last_cmd = ""

    task_json = latest / "task.json"
    if task_json.exists():
        payload = json.loads(task_json.read_text("utf-8"))
        pending_task = str(payload.get("user_goal", "")).strip()
        task_id = str(payload.get("task_id", latest.name))

    tool_trace = latest / "tool_trace.json"
    if tool_trace.exists():
        payload = json.loads(tool_trace.read_text("utf-8"))
        tool_calls = payload.get("tool_calls", [])
        if isinstance(tool_calls, list) and tool_calls:
            last = tool_calls[-1]
            if isinstance(last, dict):
                tool_name = str(last.get("tool") or last.get("name") or "").strip()
                output_summary = str(last.get("output_summary", "")).strip()
                last_cmd = _trim(f"{tool_name} -> {output_summary}", 140)

    file_changes = latest / "file_changes.json"
    if file_changes.exists():
        payload = json.loads(file_changes.read_text("utf-8"))
        changes = payload.get("file_changes", [])
        if isinstance(changes, list) and changes:
            last = changes[-1]
            if isinstance(last, dict):
                recent_file = str(last.get("path", "")).strip()

    return task_id, pending_task, recent_file, last_cmd


def _recent_session_signals(
    *,
    sessions_root: Path = DEFAULT_SESSIONS_ROOT,
    archived_root: Path = DEFAULT_ARCHIVED_ROOT,
) -> tuple[str, str]:
    recent_reasoning = ""
    recent_patch = ""
    for session_file in reversed(discover_session_files(sessions_root, archived_root)):
        try:
            lines = session_file.read_text("utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for raw_line in reversed(lines):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            normalized = normalize_session_event(record, session_file)
            if normalized is None:
                continue
            source = str(normalized.get("source", ""))
            content = str(normalized.get("content", "")).strip()
            if not recent_reasoning and source == "codex_response_item:reasoning":
                recent_reasoning = _trim(content, 220)
            elif not recent_patch and source == "codex_event:patch_apply_end":
                recent_patch = _trim(content, 220)
            if recent_reasoning and recent_patch:
                return recent_reasoning, recent_patch
    return recent_reasoning, recent_patch


def expand_short_command(task: str, *, task_runs_root: Path) -> str:
    tokens = [token for token in task.split() if token.strip()]
    if len(tokens) > 5:
        return task
    recent_task_id, pending_task, recent_file, last_cmd = _latest_task_snapshot(task_runs_root)
    parts = [task]
    if pending_task:
        parts.append(f"Recent pending task: {pending_task}")
    if recent_file:
        parts.append(f"Recent file: {recent_file}")
    if last_cmd:
        parts.append(f"Recent command result: {last_cmd}")
    if recent_task_id:
        parts.append(f"Recent task id: {recent_task_id}")
    return "\n".join(parts)


def build_dynamic_snapshot(
    task: str,
    *,
    task_runs_root: Path,
    workspace_root: Path,
    sessions_root: Path = DEFAULT_SESSIONS_ROOT,
    archived_root: Path = DEFAULT_ARCHIVED_ROOT,
) -> DynamicSnapshot:
    expanded_task = expand_short_command(task, task_runs_root=task_runs_root)
    recent_task_id, pending_task, recent_file, last_cmd = _latest_task_snapshot(task_runs_root)
    recent_reasoning, recent_patch = _recent_session_signals(
        sessions_root=sessions_root,
        archived_root=archived_root,
    )
    current_focus = pending_task or task
    return DynamicSnapshot(
        working_dir=_infer_working_dir(task),
        last_cmd=last_cmd or "No recent command recorded",
        pending_task=pending_task or "No pending task recorded",
        current_focus=_trim(current_focus, 140),
        recent_reasoning=recent_reasoning or "No recent reasoning snapshot recorded",
        recent_patch=recent_patch or "No recent patch snapshot recorded",
        recent_task_id=recent_task_id or "unknown",
        recent_file=recent_file or "unknown",
        expanded_task=expanded_task,
    )


def format_field_report(snapshot: DynamicSnapshot) -> str:
    return "\n".join(
        [
            "<field_report>",
            f"- Working Dir: {snapshot.working_dir}",
            f"- Last Cmd: {snapshot.last_cmd}",
            f"- Pending Task: {snapshot.pending_task}",
            f"- Current Focus: {snapshot.current_focus}",
            f"- Recent Reasoning: {snapshot.recent_reasoning}",
            f"- Recent Patch: {snapshot.recent_patch}",
            f"- Recent Task ID: {snapshot.recent_task_id}",
            f"- Recent File: {snapshot.recent_file}",
            "</field_report>",
        ]
    )
