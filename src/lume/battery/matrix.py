"""Expert battery matrix orchestration for Digital Sun 1.0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lume.execution import OllamaLocalHandler

from .experts import load_expert_profiles
from .router import ExpertDispatch, dispatch_expert


@dataclass(slots=True)
class BatteryMatrixResult:
    """Result of a battery-matrix completion."""

    dispatch: ExpertDispatch
    output: str
    local_model: str
    adapter: str | None
    cascade_outputs: list[dict[str, Any]]


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
        context_report: str | None = None,
        privacy_sensitive: bool = False,
        confidence_threshold: float = 0.42,
        max_experts: int = 3,
    ) -> BatteryMatrixResult:
        if not self.experts:
            raise RuntimeError("Battery matrix has no configured experts.")

        dispatch = dispatch_expert(
            task,
            self.experts,
            confidence_threshold=confidence_threshold,
            privacy_sensitive=privacy_sensitive,
            max_experts=max_experts,
        )
        cascade_outputs: list[dict[str, Any]] = []
        previous_output = ""

        for index, expert in enumerate(dispatch.cascade_experts, start=1):
            handler = self._handler_for(expert)
            if index == 1:
                prompt = (
                    f"You are the '{expert.name}' expert battery for domain "
                    f"'{expert.domain}'.\n"
                    f"Description: {expert.description}\n"
                    f"{context_report + chr(10) if context_report else ''}"
                    f"Task: {task}\n"
                    "Produce a concise local-first plan or answer that fits the current task."
                )
            else:
                prompt = (
                    f"You are the '{expert.name}' expert battery for domain "
                    f"'{expert.domain}'.\n"
                    f"Description: {expert.description}\n"
                    f"{context_report + chr(10) if context_report else ''}"
                    f"Task: {task}\n"
                    f"Primary local draft:\n{previous_output}\n\n"
                    "Refine, tighten, or extend the draft from your domain perspective. "
                    "Return only the improved local result."
                )
            output = handler.complete(prompt)
            previous_output = output
            cascade_outputs.append(
                {
                    "step": index,
                    "expert_name": expert.name,
                    "domain": expert.domain,
                    "model": expert.model,
                    "adapter": expert.adapter,
                    "matched_keywords": dispatch.cascade_matched_keywords.get(expert.name, []),
                    "output": output,
                }
            )

        return BatteryMatrixResult(
            dispatch=dispatch,
            output=previous_output,
            local_model=dispatch.primary_expert.model,
            adapter=dispatch.primary_expert.adapter,
            cascade_outputs=cascade_outputs,
        )
