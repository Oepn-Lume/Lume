"""Provider selection for synthetic teacher/judge generation."""

from __future__ import annotations

import json
from typing import Protocol

from lume.execution import OpenAICloudHandler

from .judge import JudgeModel, MockJudge
from .schema import GeneratedTask
from .teacher import MockTeacher, TeacherModel


class CloudTeacher:
    """Teacher backed by a cloud completion handler."""

    def __init__(self, model_name: str, handler: OpenAICloudHandler) -> None:
        self.model_name = model_name
        self._handler = handler

    def generate(self, task: GeneratedTask) -> str:
        prompt = (
            "You are generating a high-quality supervised fine-tuning answer.\n"
            f"Category: {task.category}\n"
            f"Difficulty: {task.difficulty}\n"
            f"Task: {task.prompt}\n\n"
            "Return only the answer content. Make it structured, reusable, and concise."
        )
        return self._handler.complete(prompt).strip()


class JudgeModel(Protocol):
    model_name: str

    def score(self, task: GeneratedTask, answer: str) -> tuple[float, str]:
        ...


class CloudJudge:
    """Judge backed by a cloud completion handler."""

    def __init__(self, model_name: str, handler: OpenAICloudHandler) -> None:
        self.model_name = model_name
        self._handler = handler

    def score(self, task: GeneratedTask, answer: str) -> tuple[float, str]:
        prompt = (
            "Score this supervised fine-tuning sample from 0.0 to 1.0.\n"
            "Return compact JSON with keys: score, rationale.\n"
            f"Task: {task.prompt}\n"
            f"Answer: {answer}"
        )
        response = self._handler.complete(prompt).strip()
        try:
            payload = json.loads(response)
            score = float(payload.get("score", 0.0))
            rationale = str(payload.get("rationale", "No rationale provided."))
        except Exception:
            score = 0.0
            rationale = f"Judge response parsing failed: {response[:200]}"
        score = max(0.0, min(score, 1.0))
        return score, rationale


def provider_has_real_cloud(provider: str) -> bool:
    if provider == "mock":
        return False
    if provider == "openai":
        handler = OpenAICloudHandler(model="gpt-5")
        return bool(handler.available)
    raise ValueError(f"Unsupported provider: {provider}")


def build_teacher(provider: str, *, require_real_cloud: bool = False) -> TeacherModel:
    if provider == "mock":
        if require_real_cloud:
            raise RuntimeError("Real cloud mode was requested, but provider=mock cannot satisfy it.")
        return MockTeacher()
    if provider == "openai":
        handler = OpenAICloudHandler(model="gpt-5")
        if handler.available:
            return CloudTeacher("openai-gpt-5", handler)
        if require_real_cloud:
            raise RuntimeError(
                "Real cloud mode was requested, but no available OpenAI cloud handler was found."
            )
        return MockTeacher(model_name="mock-teacher-fallback")
    raise ValueError(f"Unsupported provider: {provider}")


def build_judge(provider: str, *, require_real_cloud: bool = False) -> JudgeModel:
    if provider == "mock":
        if require_real_cloud:
            raise RuntimeError("Real cloud mode was requested, but provider=mock cannot satisfy it.")
        return MockJudge()
    if provider == "openai":
        handler = OpenAICloudHandler(model="gpt-5")
        if handler.available:
            return CloudJudge("openai-gpt-5-judge", handler)
        if require_real_cloud:
            raise RuntimeError(
                "Real cloud mode was requested, but no available OpenAI cloud judge handler was found."
            )
        return MockJudge(model_name="mock-judge-fallback")
    raise ValueError(f"Unsupported provider: {provider}")
