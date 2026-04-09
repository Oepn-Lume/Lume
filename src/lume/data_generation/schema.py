"""Schemas for synthetic task and sample generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GeneratedTask:
    """A parameterized task instance for teacher/judge generation."""

    task_id: str
    category: str
    template_id: str
    prompt: str
    difficulty: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GeneratedSample:
    """A final trainable sample with quality metadata."""

    task_id: str
    category: str
    input: str
    target: str
    quality_score: float
    teacher_model: str
    judge_model: str
    source_type: str
    accepted: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
