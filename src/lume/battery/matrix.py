"""Expert battery matrix orchestration for Digital Sun 1.0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lume.execution import OllamaLocalHandler

from .experts import ExpertProfile, load_expert_profiles
from .router import ExpertDispatch, dispatch_expert


@dataclass(slots=True)
class BatteryMatrixResult:
    """Result of a battery-matrix completion."""

    dispatch: ExpertDispatch
    output: str
    local_model: str
    adapter: str | None


class BatteryMatrix:
    """A small MoE-style edge battery that routes to specialist local experts."""

    def __init__(
        self,
        *,
        config_path: Path,
        endpoint: str = "http://127.0.0.1:11434/api/generate",
        tags_endpoint: str = "http://127.0.0.1:11434/api/tags",
        timeout: int = 120,
        temperature: float = 0.2,
    ) -> None:
        self.config_path = config_path
        self.endpoint = endpoint
        self.tags_endpoint = tags_endpoint
        self.timeout = timeout
        self.temperature = temperature
        self.experts = load_expert_profiles(config_path)

    @property
    def available(self) -> bool:
        if not self.experts:
            return False
        seen_models = {expert.model for expert in self.experts}
        for model in seen_models:
            handler = OllamaLocalHandler(
                model=model,
                endpoint=self.endpoint,
                tags_endpoint=self.tags_endpoint,
                timeout=self.timeout,
                temperature=self.temperature,
            )
            if handler.available:
                return True
        return False

    def _handler_for(self, expert: ExpertProfile) -> OllamaLocalHandler:
        return OllamaLocalHandler(
            model=expert.model,
            endpoint=self.endpoint,
            tags_endpoint=self.tags_endpoint,
            timeout=self.timeout,
            temperature=self.temperature,
        )

    def complete(
        self,
        task: str,
        *,
        privacy_sensitive: bool = False,
        confidence_threshold: float = 0.42,
    ) -> BatteryMatrixResult:
        if not self.experts:
            raise RuntimeError("Battery matrix has no configured experts.")

        dispatch = dispatch_expert(
            task,
            self.experts,
            confidence_threshold=confidence_threshold,
            privacy_sensitive=privacy_sensitive,
        )
        handler = self._handler_for(dispatch.primary_expert)
        prompt = (
            f"You are the '{dispatch.primary_expert.name}' expert battery for domain "
            f"'{dispatch.primary_expert.domain}'.\n"
            f"Description: {dispatch.primary_expert.description}\n"
            f"Task: {task}\n"
            "Produce a concise local-first plan or answer that fits the current task."
        )
        output = handler.complete(prompt)
        return BatteryMatrixResult(
            dispatch=dispatch,
            output=output,
            local_model=dispatch.primary_expert.model,
            adapter=dispatch.primary_expert.adapter,
        )
