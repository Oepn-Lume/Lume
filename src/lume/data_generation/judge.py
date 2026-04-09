"""Judge model abstraction for synthetic sample filtering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schema import GeneratedTask


class JudgeModel(Protocol):
    model_name: str

    def score(self, task: GeneratedTask, answer: str) -> tuple[float, str]:
        ...


@dataclass(slots=True)
class MockJudge:
    """Simple deterministic scorer for offline generation."""

    model_name: str = "mock-judge"

    def score(self, task: GeneratedTask, answer: str) -> tuple[float, str]:
        score = 0.65
        if len(answer) > 120:
            score += 0.1
        if task.difficulty == "high":
            score += 0.05
        if task.category in {"coding", "review", "memory"}:
            score += 0.1
        if "1." in answer and "2." in answer:
            score += 0.1
        score = min(score, 0.98)
        rationale = (
            "Accepted because the sample is structured, non-empty, and sufficiently specific "
            "for supervised fine-tuning."
        )
        return score, rationale
