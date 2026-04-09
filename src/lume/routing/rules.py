"""Rule-based task routing for the Lume prototype."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small project YAML files without external dependencies."""
    data: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in path.read_text("utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current_section = None
            else:
                data[key] = {}
                current_section = key
            continue
        if current_section and raw_line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            data[current_section][key.strip()] = value.strip().strip('"')
    return data


@dataclass(slots=True)
class RoutingDecision:
    """Structured output of the routing layer."""

    mode: str
    reasons: list[str]
    similarity_score: float
    task_complexity: str
    local_quality_score: float | None = None
    local_quality_ready: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reasons": self.reasons,
            "similarity_score": self.similarity_score,
            "task_complexity": self.task_complexity,
            "local_quality_score": self.local_quality_score,
            "local_quality_ready": self.local_quality_ready,
        }


def _read_local_quality_snapshot(path: Path | None) -> tuple[float | None, bool | None]:
    if path is None or not path.exists():
        return None, None
    payload = json.loads(path.read_text("utf-8-sig"))
    score = payload.get("local_quality_score")
    ready = payload.get("battery_model_ready")
    return (float(score) if score is not None else None, bool(ready) if ready is not None else None)


def _estimate_similarity(task: str, task_runs_root: Path) -> float:
    """Very small heuristic similarity based on word overlap with past goals."""
    words = {word.lower() for word in task.split() if word.strip()}
    if not words or not task_runs_root.exists():
        return 0.0

    best_score = 0.0
    for task_dir in task_runs_root.iterdir():
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        payload = json.loads(task_json.read_text("utf-8"))
        goal_words = {
            word.lower() for word in str(payload.get("user_goal", "")).split() if word.strip()
        }
        if not goal_words:
            continue
        overlap = len(words & goal_words)
        union = len(words | goal_words)
        if union:
            best_score = max(best_score, overlap / union)
    return round(best_score, 3)


def _estimate_complexity(task: str) -> str:
    length = len(task)
    lowered = task.lower()
    if any(keyword in lowered for keyword in ["predict", "architecture", "system", "pipeline"]):
        return "high"
    if length > 120:
        return "high"
    if length > 40:
        return "medium"
    return "low"


def route_task(
    task: str,
    *,
    routing_config_path: Path,
    task_runs_root: Path,
    cloud_available: bool = True,
    privacy_sensitive: bool = False,
    local_quality_path: Path | None = None,
) -> RoutingDecision:
    """Route a task using simple heuristics and historic similarity."""
    config = _parse_simple_yaml(routing_config_path)
    rules = config.get("rules", {})
    thresholds = config.get("thresholds", {})
    similarity_threshold = float(thresholds.get("similarity_for_local", 0.85))
    local_quality_threshold = float(thresholds.get("local_quality_for_local", 0.7))

    similarity_score = _estimate_similarity(task, task_runs_root)
    complexity = _estimate_complexity(task)
    local_quality_score, local_quality_ready = _read_local_quality_snapshot(local_quality_path)
    reasons: list[str] = []

    if not cloud_available:
        reasons.append("cloud unavailable")
        return RoutingDecision(
            mode=rules.get("cloud_unavailable", "local"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
        )

    if privacy_sensitive:
        reasons.append("privacy sensitive")
        return RoutingDecision(
            mode=rules.get("privacy_sensitive_task", "hybrid"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
        )

    if similarity_score >= similarity_threshold and complexity == "low":
        reasons.append("high similarity to prior task")
        reasons.append("low complexity")
        if local_quality_ready is False:
            reasons.append("local quality snapshot not ready")
            return RoutingDecision(
                mode=rules.get("quality_gated_task", "hybrid"),
                reasons=reasons,
                similarity_score=similarity_score,
                task_complexity=complexity,
                local_quality_score=local_quality_score,
                local_quality_ready=local_quality_ready,
            )
        if local_quality_score is not None and local_quality_score < local_quality_threshold:
            reasons.append("local quality below threshold")
            return RoutingDecision(
                mode=rules.get("quality_gated_task", "hybrid"),
                reasons=reasons,
                similarity_score=similarity_score,
                task_complexity=complexity,
                local_quality_score=local_quality_score,
                local_quality_ready=local_quality_ready,
            )
        return RoutingDecision(
            mode=rules.get("high_similarity_task", "local"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
        )

    if complexity == "high":
        reasons.append("novel or high-complexity task")
        return RoutingDecision(
            mode=rules.get("novel_complex_task", "cloud"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
        )

    reasons.append("defaulting to cloud-first for moderate certainty")
    return RoutingDecision(
        mode=config.get("default_mode", "cloud"),
        reasons=reasons,
        similarity_score=similarity_score,
        task_complexity=complexity,
        local_quality_score=local_quality_score,
        local_quality_ready=local_quality_ready,
    )
