"""Utilities for persisting session-level shadow logs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", "utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), "utf-8")


@dataclass(slots=True)
class ShadowMessage:
    """A single message in the observable conversation timeline."""

    role: str
    content: str
    source: str
    timestamp: str = field(default_factory=utc_now_iso)
    model: str | None = None
    message_type: str = "message"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "role": self.role,
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "metadata": self.metadata,
        }
        if self.model:
            payload["model"] = self.model
        return payload


@dataclass(slots=True)
class ShadowToolCall:
    """A single tool invocation or execution step."""

    tool: str
    source: str = "codex"
    status: str = "completed"
    arguments: dict[str, Any] = field(default_factory=dict)
    output_summary: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    ended_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "source": self.source,
            "status": self.status,
            "arguments": self.arguments,
            "output_summary": self.output_summary,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ShadowFileChange:
    """A normalized file change record."""

    path: str
    change_type: str = "modified"
    summary: str = ""
    source: str = "codex"
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "summary": self.summary,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ShadowLogRecord:
    """Structured session record written into the task_runs directory."""

    task_id: str
    user_goal: str
    route_mode: str
    model_used: str
    session_id: str | None = None
    cloud_model: str | None = None
    codex_model: str | None = None
    messages: list[ShadowMessage] = field(default_factory=list)
    tool_calls: list[ShadowToolCall] = field(default_factory=list)
    file_changes: list[ShadowFileChange] = field(default_factory=list)
    result_status: str = "completed"
    value_score: float = 0.0
    postmortem: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    structured_artifacts: dict[str, Any] = field(default_factory=dict)
    timestamp: str | None = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if self.session_id is None:
            self.session_id = self.task_id
        if self.timestamp is None:
            self.timestamp = utc_now_iso()
        if self.cloud_model is None and self.route_mode in {"cloud", "hybrid"}:
            self.cloud_model = self.model_used
        if self.codex_model is None:
            self.codex_model = "codex"

    @property
    def prompts(self) -> list[str]:
        return [
            message.content
            for message in self.messages
            if message.role in {"user", "system"} and message.source != "cloud"
        ]

    @property
    def responses(self) -> list[str]:
        return [
            message.content
            for message in self.messages
            if message.role == "assistant"
        ]

    def to_task_payload(self) -> dict[str, Any]:
        """Return the summary payload for task.json."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "user_goal": self.user_goal,
            "route_mode": self.route_mode,
            "model_used": self.model_used,
            "cloud_model": self.cloud_model,
            "codex_model": self.codex_model,
            "result_status": self.result_status,
            "value_score": self.value_score,
            "postmortem": self.postmortem,
            "tags": self.tags,
            "metadata": self.metadata,
            "message_count": len(self.messages),
            "tool_call_count": len(self.tool_calls),
            "file_change_count": len(self.file_changes),
        }

    def to_prompt_response_payload(self) -> dict[str, Any]:
        """Return prompt/response pairs for compatibility and quick review."""
        user_or_system = [
            message
            for message in self.messages
            if message.role in {"user", "system"} and message.source != "cloud"
        ]
        assistants = [message for message in self.messages if message.role == "assistant"]
        pair_count = min(len(user_or_system), len(assistants))
        return {
            "task_id": self.task_id,
            "pairs": [
                {
                    "prompt": user_or_system[index].content,
                    "response": assistants[index].content,
                    "prompt_source": user_or_system[index].source,
                    "response_source": assistants[index].source,
                }
                for index in range(pair_count)
            ],
            "prompt_count": len(user_or_system),
            "response_count": len(assistants),
        }

    def to_tool_trace_payload(self) -> dict[str, Any]:
        """Return tool call trace and file summary for tool_trace.json."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "tool_calls": [tool_call.to_dict() for tool_call in self.tool_calls],
            "files_changed": [file_change.path for file_change in self.file_changes],
        }

    def to_conversation_payload(self) -> list[dict[str, Any]]:
        """Return a JSONL-friendly representation of the visible message stream."""
        return [message.to_dict() for message in self.messages]

    def to_file_changes_payload(self) -> dict[str, Any]:
        """Return a full file change payload for file_changes.json."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "file_changes": [file_change.to_dict() for file_change in self.file_changes],
        }

    def to_outcome_payload(self) -> dict[str, Any]:
        """Return outcome summary for outcome.json."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "result_status": self.result_status,
            "value_score": self.value_score,
            "postmortem": self.postmortem,
            "message_count": len(self.messages),
            "tool_call_count": len(self.tool_calls),
            "file_change_count": len(self.file_changes),
        }

    def to_manifest_payload(self) -> dict[str, Any]:
        """Return a manifest for all generated session artifacts."""
        artifacts = {
            "task": "task.json",
            "prompt_response": "prompt_response.json",
            "conversation": "conversation.jsonl",
            "tool_trace": "tool_trace.json",
            "file_changes": "file_changes.json",
            "file_diff_summary": "file_diff_summary.md",
            "outcome": "outcome.json",
            "notes": "notes.md",
        }
        if self.structured_artifacts:
            artifacts["structured"] = {
                name: f"artifacts/{name}.json" for name in sorted(self.structured_artifacts)
            }
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "artifacts": artifacts,
        }

    def to_notes_markdown(self) -> str:
        """Return a readable markdown summary for quick inspection."""
        lines = [
            f"# Shadow Log {self.task_id}",
            "",
            "## Summary",
            f"- Timestamp: {self.timestamp}",
            f"- Session ID: {self.session_id}",
            f"- Route Mode: {self.route_mode}",
            f"- Model Used: {self.model_used}",
            f"- Cloud Model: {self.cloud_model or 'n/a'}",
            f"- Codex Model: {self.codex_model or 'n/a'}",
            f"- Result Status: {self.result_status}",
            f"- Value Score: {self.value_score}",
            f"- Message Count: {len(self.messages)}",
            f"- Tool Call Count: {len(self.tool_calls)}",
            f"- File Change Count: {len(self.file_changes)}",
            "",
            "## User Goal",
            self.user_goal or "_No goal provided._",
            "",
            "## Tags",
            ", ".join(self.tags) if self.tags else "_No tags provided._",
            "",
            "## Notes",
            self.notes or "_No notes provided._",
            "",
            "## Postmortem",
            self.postmortem or "_No postmortem provided._",
        ]
        return "\n".join(lines) + "\n"


class ShadowLogger:
    """Persist session logs and keep a root-level session index."""

    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    @property
    def session_index_path(self) -> Path:
        return self.output_root / "session_index.json"

    def write(self, record: ShadowLogRecord) -> Path:
        task_dir = self.output_root / record.task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        _write_json(task_dir / "task.json", record.to_task_payload())
        _write_json(
            task_dir / "prompt_response.json",
            record.to_prompt_response_payload(),
        )
        _write_jsonl(task_dir / "conversation.jsonl", record.to_conversation_payload())
        _write_json(task_dir / "tool_trace.json", record.to_tool_trace_payload())
        _write_json(task_dir / "file_changes.json", record.to_file_changes_payload())

        file_diff_summary = "\n".join(
            f"- [{change.change_type}] {change.path}: {change.summary or 'No summary'}"
            for change in record.file_changes
        ) or "- No files changed"
        (task_dir / "file_diff_summary.md").write_text(
            "# File Diff Summary\n\n" + file_diff_summary + "\n",
            "utf-8",
        )
        _write_json(task_dir / "outcome.json", record.to_outcome_payload())
        if record.structured_artifacts:
            artifacts_dir = task_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            for name, payload in record.structured_artifacts.items():
                _write_json(artifacts_dir / f"{name}.json", payload)
        _write_json(task_dir / "manifest.json", record.to_manifest_payload())
        (task_dir / "notes.md").write_text(record.to_notes_markdown(), "utf-8")

        self._update_session_index(record)
        return task_dir

    def _update_session_index(self, record: ShadowLogRecord) -> None:
        index_payload: dict[str, Any]
        if self.session_index_path.exists():
            index_payload = json.loads(self.session_index_path.read_text("utf-8"))
        else:
            index_payload = {"sessions": []}

        sessions: list[dict[str, Any]] = index_payload.setdefault("sessions", [])
        session_entry = {
            "task_id": record.task_id,
            "session_id": record.session_id,
            "timestamp": record.timestamp,
            "route_mode": record.route_mode,
            "model_used": record.model_used,
            "result_status": record.result_status,
            "value_score": record.value_score,
            "message_count": len(record.messages),
            "tool_call_count": len(record.tool_calls),
            "file_change_count": len(record.file_changes),
            "path": record.task_id,
        }

        sessions = [entry for entry in sessions if entry["task_id"] != record.task_id]
        sessions.append(session_entry)
        sessions.sort(key=lambda entry: entry["timestamp"])
        index_payload["sessions"] = sessions
        _write_json(self.session_index_path, index_payload)


def write_shadow_log(record: ShadowLogRecord, output_root: str | Path) -> Path:
    """Persist a task record into a task-specific directory."""
    return ShadowLogger(output_root).write(record)
