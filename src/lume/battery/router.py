"""Smart gating router for the Digital Sun expert battery matrix."""

from __future__ import annotations

from dataclasses import dataclass

from .experts import ExpertProfile


@dataclass(slots=True)
class ExpertDispatch:
    """Structured dispatch result for a battery expert selection."""

    primary_expert: ExpertProfile
    cascade_experts: list[ExpertProfile]
    confidence: float
    secondary_confidence: float | None
    cloud_assist_recommended: bool
    privacy_sensitive: bool
    matched_keywords: list[str]
    cascade_matched_keywords: dict[str, list[str]]
    candidate_scores: dict[str, float]
    selected_expert_count: int


def _task_keywords(task: str) -> list[str]:
    return [token.strip(".,:;!?()[]{}").lower() for token in task.split() if token.strip()]


def _dynamic_expert_limit(
    ranked: list[tuple[ExpertProfile, float]],
    candidate_matches: dict[str, list[str]],
    *,
    max_experts: int,
) -> int:
    if not ranked:
        return 1
    if max_experts <= 1:
        return 1

    primary_score = ranked[0][1]
    secondary_score = ranked[1][1] if len(ranked) > 1 else 0.0
    tertiary_score = ranked[2][1] if len(ranked) > 2 else 0.0
    top_match_count = len(candidate_matches.get(ranked[0][0].name, []))

    if primary_score >= 0.7 and secondary_score < 0.35 and top_match_count >= 2:
        return 1
    if tertiary_score >= 0.3 and secondary_score >= 0.35 and max_experts >= 3:
        return 3
    if secondary_score >= 0.2:
        return min(2, max_experts)
    return 1


def dispatch_expert(
    task: str,
    experts: list[ExpertProfile],
    *,
    confidence_threshold: float = 0.42,
    privacy_sensitive: bool = False,
    max_experts: int = 3,
) -> ExpertDispatch:
    """Choose the most suitable expert battery cascade for a task."""
    tokens = _task_keywords(task)
    token_set = set(tokens)

    candidate_scores: dict[str, float] = {}
    candidate_matches: dict[str, list[str]] = {}
    ranked: list[tuple[ExpertProfile, float]] = []

    for expert in experts:
        matches = sorted(keyword for keyword in expert.keywords if keyword in token_set)
        keyword_score = len(matches) / max(len(expert.keywords), 1)
        privacy_bonus = 0.2 if privacy_sensitive and expert.privacy_sensitive else 0.0
        general_bonus = 0.1 if expert.domain == "general" else 0.0
        score = keyword_score + expert.confidence_bias + privacy_bonus + general_bonus
        score = round(min(score, 1.0), 3)
        candidate_scores[expert.name] = score
        candidate_matches[expert.name] = matches
        ranked.append((expert, score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    selected_count = _dynamic_expert_limit(
        ranked,
        candidate_matches,
        max_experts=max(1, max_experts),
    )
    cascade = [expert for expert, _score in ranked[:selected_count]]
    primary_expert = cascade[0]
    best_score = ranked[0][1]
    secondary_confidence = ranked[1][1] if len(ranked) > 1 and len(cascade) > 1 else None
    best_matches = candidate_matches.get(primary_expert.name, [])

    cloud_assist_recommended = best_score < confidence_threshold
    return ExpertDispatch(
        primary_expert=primary_expert,
        cascade_experts=cascade,
        confidence=best_score,
        secondary_confidence=secondary_confidence,
        cloud_assist_recommended=cloud_assist_recommended,
        privacy_sensitive=privacy_sensitive,
        matched_keywords=best_matches,
        cascade_matched_keywords={
            expert.name: candidate_matches.get(expert.name, [])
            for expert in cascade
        },
        candidate_scores=candidate_scores,
        selected_expert_count=len(cascade),
    )
