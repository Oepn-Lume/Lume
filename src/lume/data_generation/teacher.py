"""Teacher model abstraction for synthetic supervised sample generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schema import GeneratedTask


class TeacherModel(Protocol):
    model_name: str

    def generate(self, task: GeneratedTask) -> str:
        ...


@dataclass(slots=True)
class MockTeacher:
    """Deterministic fallback teacher for offline data generation."""

    model_name: str = "mock-teacher"

    def generate(self, task: GeneratedTask) -> str:
        return (
            f"Category: {task.category}\n"
            f"Difficulty: {task.difficulty}\n"
            f"Task: {task.prompt}\n\n"
            "Answer:\n"
            "1. Clarify the user's goal.\n"
            "2. Provide a structured, reusable response.\n"
            "3. Include practical next steps and key cautions.\n"
            "4. Keep the tone concise, useful, and training-worthy.\n"
        )
