"""Execution-session helpers that wire runtime events into shadow logging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lume.logging import ShadowSessionRecorder


class ExecutionSession:
    """Thin wrapper around the shadow recorder for Codex-style execution flows."""

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
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.recorder = ShadowSessionRecorder(
            task_id=task_id,
            user_goal=user_goal,
            route_mode=route_mode,
            model_used=model_used,
            output_root=output_root,
            session_id=session_id,
            cloud_model=cloud_model,
            codex_model=codex_model,
            metadata=metadata,
        )

    def user(self, content: str, **metadata: Any) -> None:
        self.recorder.add_user_message(content, **metadata)

    def cloud(
        self,
        content: str,
        *,
        role: str = "assistant",
        model: str | None = None,
        message_type: str = "message",
        **metadata: Any,
    ) -> None:
        self.recorder.add_cloud_message(
            content,
            role=role,
            model=model,
            message_type=message_type,
            **metadata,
        )

    def codex(
        self,
        content: str,
        *,
        role: str = "assistant",
        model: str | None = None,
        message_type: str = "message",
        **metadata: Any,
    ) -> None:
        self.recorder.add_codex_message(
            content,
            role=role,
            model=model,
            message_type=message_type,
            **metadata,
        )

    def tool(
        self,
        tool: str,
        *,
        source: str = "codex",
        status: str = "completed",
        arguments: dict[str, Any] | None = None,
        output_summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.recorder.add_tool_call(
            tool=tool,
            source=source,
            status=status,
            arguments=arguments,
            output_summary=output_summary,
            metadata=metadata,
        )

    def file(
        self,
        path: str,
        *,
        change_type: str = "modified",
        summary: str = "",
        source: str = "codex",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.recorder.add_file_change(
            path=path,
            change_type=change_type,
            summary=summary,
            source=source,
            metadata=metadata,
        )

    def finish(
        self,
        *,
        result_status: str = "completed",
        value_score: float = 0.0,
        postmortem: str = "",
        notes: str = "",
    ) -> Path:
        self.recorder.finalize(
            result_status=result_status,
            value_score=value_score,
            postmortem=postmortem,
            notes=notes,
        )
        return self.recorder.flush()
