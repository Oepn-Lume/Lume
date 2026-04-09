"""Runtime-friendly recorder for session-level shadow logging."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from .shadow import (
    ShadowFileChange,
    ShadowLogRecord,
    ShadowLogger,
    ShadowMessage,
    ShadowToolCall,
)


class ShadowSessionRecorder:
    """Incrementally build and persist a shadow log for a live session."""

    def __init__(
        self,
        *,
        task_id: str,
        user_goal: str,
        route_mode: str,
        model_used: str,
        output_root: str | Path,
        session_id: str | None = None,
        cloud_model: str | None = None,
        codex_model: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._logger = ShadowLogger(output_root)
        self._record = ShadowLogRecord(
            task_id=task_id,
            user_goal=user_goal,
            route_mode=route_mode,
            model_used=model_used,
            session_id=session_id,
            cloud_model=cloud_model,
            codex_model=codex_model,
            tags=list(tags or []),
            metadata=dict(metadata or {}),
        )

    @property
    def record(self) -> ShadowLogRecord:
        """Expose the current in-memory record."""
        return self._record

    def add_message(
        self,
        *,
        role: str,
        content: str,
        source: str,
        model: str | None = None,
        message_type: str = "message",
        metadata: dict[str, Any] | None = None,
    ) -> ShadowMessage:
        message = ShadowMessage(
            role=role,
            content=content,
            source=source,
            model=model,
            message_type=message_type,
            metadata=dict(metadata or {}),
        )
        self._record.messages.append(message)
        return message

    def add_user_message(self, content: str, **metadata: Any) -> ShadowMessage:
        return self.add_message(
            role="user",
            content=content,
            source="user",
            metadata=metadata,
        )

    def add_cloud_message(
        self,
        content: str,
        *,
        role: str = "assistant",
        model: str | None = None,
        message_type: str = "message",
        **metadata: Any,
    ) -> ShadowMessage:
        return self.add_message(
            role=role,
            content=content,
            source="cloud",
            model=model or self._record.cloud_model,
            message_type=message_type,
            metadata=metadata,
        )

    def add_codex_message(
        self,
        content: str,
        *,
        role: str = "assistant",
        model: str | None = None,
        message_type: str = "message",
        **metadata: Any,
    ) -> ShadowMessage:
        return self.add_message(
            role=role,
            content=content,
            source="codex",
            model=model or self._record.codex_model,
            message_type=message_type,
            metadata=metadata,
        )

    def add_tool_call(
        self,
        *,
        tool: str,
        source: str = "codex",
        status: str = "completed",
        arguments: dict[str, Any] | None = None,
        output_summary: str = "",
        ended_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ShadowToolCall:
        tool_call = ShadowToolCall(
            tool=tool,
            source=source,
            status=status,
            arguments=dict(arguments or {}),
            output_summary=output_summary,
            ended_at=ended_at,
            metadata=dict(metadata or {}),
        )
        self._record.tool_calls.append(tool_call)
        return tool_call

    def add_file_change(
        self,
        *,
        path: str,
        change_type: str = "modified",
        summary: str = "",
        source: str = "codex",
        metadata: dict[str, Any] | None = None,
    ) -> ShadowFileChange:
        file_change = ShadowFileChange(
            path=path,
            change_type=change_type,
            summary=summary,
            source=source,
            metadata=dict(metadata or {}),
        )
        self._record.file_changes.append(file_change)
        return file_change

    def add_tag(self, tag: str) -> None:
        if tag not in self._record.tags:
            self._record.tags.append(tag)

    def update_metadata(self, **metadata: Any) -> None:
        self._record.metadata.update(metadata)

    def finalize(
        self,
        *,
        result_status: str | None = None,
        value_score: float | None = None,
        postmortem: str | None = None,
        notes: str | None = None,
    ) -> None:
        if result_status is not None:
            self._record.result_status = result_status
        if value_score is not None:
            self._record.value_score = value_score
        if postmortem is not None:
            self._record.postmortem = postmortem
        if notes is not None:
            self._record.notes = notes

    def flush(self) -> Path:
        return self._logger.write(self._record)

    def snapshot(self) -> ShadowLogRecord:
        """Return a copy of the current record for inspection without flushing."""
        return replace(
            self._record,
            messages=list(self._record.messages),
            tool_calls=list(self._record.tool_calls),
            file_changes=list(self._record.file_changes),
            tags=list(self._record.tags),
            metadata=dict(self._record.metadata),
        )
