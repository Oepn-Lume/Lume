"""Runtime adapters that auto-capture cloud and Codex activity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .session import ExecutionSession


CloudHandler = Callable[[str], str]
CodexHandler = Callable[[str], str]


@dataclass(slots=True)
class RuntimeModels:
    """Model identities used by the observed runtime."""

    primary: str
    cloud: str
    codex: str


class ObservedCloudModel:
    """Wrap a cloud callable and log all visible prompts and responses."""

    def __init__(
        self,
        session: ExecutionSession,
        *,
        handler: CloudHandler,
        model_name: str,
    ) -> None:
        self._session = session
        self._handler = handler
        self._model_name = model_name

    def complete(
        self,
        prompt: str,
        *,
        message_type: str = "message",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._session.cloud(
            prompt,
            role="system",
            model=self._model_name,
            message_type="prompt",
            **dict(metadata or {}),
        )
        response = self._handler(prompt)
        self._session.cloud(
            response,
            role="assistant",
            model=self._model_name,
            message_type=message_type,
            **dict(metadata or {}),
        )
        return response


class ObservedCodexExecutor:
    """Wrap Codex-visible actions and persist them automatically."""

    def __init__(
        self,
        session: ExecutionSession,
        *,
        handler: CodexHandler,
        model_name: str,
    ) -> None:
        self._session = session
        self._handler = handler
        self._model_name = model_name

    def respond(
        self,
        instruction: str,
        *,
        message_type: str = "message",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        response = self._handler(instruction)
        self._session.codex(
            response,
            role="assistant",
            model=self._model_name,
            message_type=message_type,
            **dict(metadata or {}),
        )
        return response

    def tool(
        self,
        tool: str,
        *,
        status: str = "completed",
        arguments: dict[str, Any] | None = None,
        output_summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._session.tool(
            tool,
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
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._session.file(
            path,
            change_type=change_type,
            summary=summary,
            metadata=metadata,
        )


class ObservedRuntime:
    """High-level runtime that records user, cloud, and Codex events invisibly."""

    def __init__(
        self,
        *,
        task_id: str,
        user_goal: str,
        route_mode: str,
        output_root: str | Path,
        models: RuntimeModels,
        cloud_handler: CloudHandler,
        codex_handler: CodexHandler,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.session = ExecutionSession(
            task_id=task_id,
            user_goal=user_goal,
            route_mode=route_mode,
            model_used=models.primary,
            output_root=output_root,
            cloud_model=models.cloud,
            codex_model=models.codex,
            metadata=metadata,
        )
        self.cloud = ObservedCloudModel(
            self.session,
            handler=cloud_handler,
            model_name=models.cloud,
        )
        self.codex = ObservedCodexExecutor(
            self.session,
            handler=codex_handler,
            model_name=models.codex,
        )

    def user(self, content: str, **metadata: Any) -> None:
        self.session.user(content, **metadata)

    def finish(
        self,
        *,
        result_status: str = "completed",
        value_score: float = 0.0,
        postmortem: str = "",
        notes: str = "",
    ) -> Path:
        return self.session.finish(
            result_status=result_status,
            value_score=value_score,
            postmortem=postmortem,
            notes=notes,
        )
