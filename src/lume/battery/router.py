"""Smart gating router for the Digital Sun expert battery matrix."""

from __future__ import annotations

from dataclasses import dataclass

from .experts import ExpertProfile


@dataclass(slots=True)
class ExpertDispatch:
    """Structured dispatch result for a battery expert selection."""

    primary_expert: ExpertProfile
    confidence: float
    cloud_assist_recommended: bool
    privacy_sensitive: bool
    matched_keywords: list[str]
    candidate_scores: dict[str, float]


def _task_keywords(task: str) -> list[str]:
    return [token.strip(".,:;!?()[]{}").lower() for token in task.split() if token.strip()]


def dispatch_expert(
    task: str,
    experts: list[ExpertProfile],
    *,
    confidence_threshold: float = 0.42,
    privacy_sensitive: bool = False,
) -> ExpertDispatch:
    """Choose the most suitable expert battery for a task."""
    tokens = _task_keywords(task)
    token_set = set(tokens)

    best_expert = experts[0]
    best_score = -1.0
    best_matches: list[str] = []
    candidate_scores: dict[str, float] = {}

    for expert in experts:
        matches = sorted(keyword for keyword in expert.keywords if keyword in token_set)
        keyword_score = len(matches) / max(len(expert.keywords), 1)
        privacy_bonus = 0.2 if privacy_sensitive and expert.privacy_sensitive else 0.0
        general_bonus = 0.1 if expert.domain == "general" else 0.0
        score = keyword_score + expert.confidence_bias + privacy_bonus + general_bonus
        score = round(min(score, 1.0), 3)
        candidate_scores[expert.name] = score
        if score > best_score:
            best_expert = expert
            best_score = score
            best_matches = matches

    cloud_assist_recommended = best_score < confidence_threshold
    return ExpertDispatch(
        primary_expert=best_expert,
        confidence=best_score,
        cloud_assist_recommended=cloud_assist_recommended,
        privacy_sensitive=privacy_sensitive,
        matched_keywords=best_matches,
        candidate_scores=candidate_scores,
    )
