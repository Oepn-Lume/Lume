"""Rule-based task routing for the Lume prototype."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from lume.codex import classify_codex_action, codex_action_readiness_key


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
    adaptive_local_quality_score: float | None = None
    adaptive_local_threshold: float | None = None
    action_task: bool | None = None
    codex_action_label: str | None = None
    codex_action_readiness: float | None = None
    action_specific_readiness: float | None = None
    action_specific_threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reasons": self.reasons,
            "similarity_score": self.similarity_score,
            "task_complexity": self.task_complexity,
            "local_quality_score": self.local_quality_score,
            "local_quality_ready": self.local_quality_ready,
            "adaptive_local_quality_score": self.adaptive_local_quality_score,
            "adaptive_local_threshold": self.adaptive_local_threshold,
            "action_task": self.action_task,
            "codex_action_label": self.codex_action_label,
            "codex_action_readiness": self.codex_action_readiness,
            "action_specific_readiness": self.action_specific_readiness,
            "action_specific_threshold": self.action_specific_threshold,
        }


ACTION_KEYWORDS = {
    "continue",
    "publish",
    "fix",
    "implement",
    "retry",
    "next",
    "deploy",
    "debug",
    "repair",
    "ship",
    "release",
    "继续",
    "发布",
    "修复",
    "实现",
    "重试",
    "下一步",
    "部署",
}


def _read_local_quality_snapshot(path: Path | None) -> tuple[float | None, bool | None, float | None, float | None, dict[str, float]]:
    if path is None or not path.exists():
        return None, None, None, None, {}
    payload = json.loads(path.read_text("utf-8-sig"))
    score = payload.get("local_quality_score")
    adaptive_score = payload.get("adaptive_local_quality_score")
    adaptive_threshold = payload.get("adaptive_local_threshold")
    ready = payload.get("battery_model_ready")
    readiness = {
        "codex_action_readiness": float(payload["codex_action_readiness"])
        if payload.get("codex_action_readiness") is not None
        else 0.0,
        "continue_action_readiness": float(payload["continue_action_readiness"])
        if payload.get("continue_action_readiness") is not None
        else 0.0,
        "patch_action_readiness": float(payload["patch_action_readiness"])
        if payload.get("patch_action_readiness") is not None
        else 0.0,
        "log_action_readiness": float(payload["log_action_readiness"])
        if payload.get("log_action_readiness") is not None
        else 0.0,
    }
    return (
        float(score) if score is not None else None,
        bool(ready) if ready is not None else None,
        float(adaptive_score) if adaptive_score is not None else None,
        float(adaptive_threshold) if adaptive_threshold is not None else None,
        readiness,
    )


def _is_action_task(task: str) -> bool:
    tokens = [word.strip(".,:;!?()[]{}").lower() for word in task.split() if word.strip()]
    decision = classify_codex_action(task)
    return len(tokens) <= 5 and (
        any(token in ACTION_KEYWORDS for token in tokens)
        or decision.action_label in {"continue_task", "prepare_patch", "inspect_log", "publish_release"}
    )


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
    codex_action_threshold = float(thresholds.get("codex_action_readiness_for_local", 0.6))
    continue_action_threshold = float(thresholds.get("continue_action_readiness_for_local", codex_action_threshold))
    patch_action_threshold = float(thresholds.get("patch_action_readiness_for_local", codex_action_threshold))
    log_action_threshold = float(thresholds.get("log_action_readiness_for_local", codex_action_threshold))

    similarity_score = _estimate_similarity(task, task_runs_root)
    complexity = _estimate_complexity(task)
    local_quality_score, local_quality_ready, adaptive_local_quality_score, adaptive_local_threshold, readiness_map = _read_local_quality_snapshot(local_quality_path)
    reasons: list[str] = []
    action_task = _is_action_task(task)
    codex_action = classify_codex_action(task)
    codex_action_readiness = readiness_map.get("codex_action_readiness")
    action_specific_key = codex_action_readiness_key(codex_action.action_label)
    action_specific_readiness = readiness_map.get(action_specific_key) if action_specific_key else codex_action_readiness
    action_threshold_map = {
        "continue_action_readiness": continue_action_threshold,
        "patch_action_readiness": patch_action_threshold,
        "log_action_readiness": log_action_threshold,
    }
    action_specific_threshold = action_threshold_map.get(action_specific_key, codex_action_threshold)
    effective_local_quality = adaptive_local_quality_score if adaptive_local_quality_score is not None else local_quality_score
    effective_local_threshold = adaptive_local_threshold if adaptive_local_threshold is not None else local_quality_threshold

    if not cloud_available:
        reasons.append("cloud unavailable")
        return RoutingDecision(
            mode=rules.get("cloud_unavailable", "local"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
            adaptive_local_quality_score=adaptive_local_quality_score,
            adaptive_local_threshold=adaptive_local_threshold,
            action_task=action_task,
            codex_action_label=codex_action.action_label,
            codex_action_readiness=codex_action_readiness,
            action_specific_readiness=action_specific_readiness,
            action_specific_threshold=action_specific_threshold,
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
            adaptive_local_quality_score=adaptive_local_quality_score,
            adaptive_local_threshold=adaptive_local_threshold,
            action_task=action_task,
            codex_action_label=codex_action.action_label,
            codex_action_readiness=codex_action_readiness,
            action_specific_readiness=action_specific_readiness,
            action_specific_threshold=action_specific_threshold,
        )

    if similarity_score >= similarity_threshold and complexity == "low":
        reasons.append("high similarity to prior task")
        reasons.append("low complexity")
        if action_task:
            reasons.append("short action command")
        if local_quality_ready is False:
            reasons.append("local quality snapshot not ready")
            return RoutingDecision(
                mode=rules.get("quality_gated_task", "hybrid"),
                reasons=reasons,
                similarity_score=similarity_score,
                task_complexity=complexity,
                local_quality_score=local_quality_score,
                local_quality_ready=local_quality_ready,
                adaptive_local_quality_score=adaptive_local_quality_score,
                adaptive_local_threshold=adaptive_local_threshold,
                action_task=action_task,
                codex_action_label=codex_action.action_label,
                codex_action_readiness=codex_action_readiness,
                action_specific_readiness=action_specific_readiness,
                action_specific_threshold=action_specific_threshold,
            )
        if effective_local_quality is not None and effective_local_quality < effective_local_threshold:
            reasons.append("local quality below threshold")
            return RoutingDecision(
                mode=rules.get("quality_gated_task", "hybrid"),
                reasons=reasons,
                similarity_score=similarity_score,
                task_complexity=complexity,
                local_quality_score=local_quality_score,
                local_quality_ready=local_quality_ready,
                adaptive_local_quality_score=adaptive_local_quality_score,
                adaptive_local_threshold=adaptive_local_threshold,
                action_task=action_task,
                codex_action_label=codex_action.action_label,
                codex_action_readiness=codex_action_readiness,
                action_specific_readiness=action_specific_readiness,
                action_specific_threshold=action_specific_threshold,
            )
        return RoutingDecision(
            mode=rules.get("high_similarity_task", "local"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
            adaptive_local_quality_score=adaptive_local_quality_score,
            adaptive_local_threshold=adaptive_local_threshold,
            action_task=action_task,
            codex_action_label=codex_action.action_label,
            codex_action_readiness=codex_action_readiness,
            action_specific_readiness=action_specific_readiness,
            action_specific_threshold=action_specific_threshold,
        )

    if action_task and complexity == "low":
        reasons.append("short action command")
        reasons.append(f"codex action label: {codex_action.action_label}")
        if action_specific_key:
            reasons.append(f"action readiness key: {action_specific_key}")
        if (
            local_quality_ready
            and effective_local_quality is not None
            and effective_local_quality >= effective_local_threshold
            and action_specific_readiness is not None
            and action_specific_readiness >= action_specific_threshold
        ):
            reasons.append("adaptive local quality ready")
            reasons.append("action-specific readiness above threshold")
            return RoutingDecision(
                mode=rules.get("action_task_when_ready", "local"),
                reasons=reasons,
                similarity_score=similarity_score,
                task_complexity=complexity,
                local_quality_score=local_quality_score,
                local_quality_ready=local_quality_ready,
                adaptive_local_quality_score=adaptive_local_quality_score,
                adaptive_local_threshold=adaptive_local_threshold,
                action_task=action_task,
                codex_action_label=codex_action.action_label,
                codex_action_readiness=codex_action_readiness,
                action_specific_readiness=action_specific_readiness,
                action_specific_threshold=action_specific_threshold,
            )
        reasons.append("action task still needs cloud assist")
        return RoutingDecision(
            mode=rules.get("action_task_when_unready", "hybrid"),
            reasons=reasons,
            similarity_score=similarity_score,
            task_complexity=complexity,
            local_quality_score=local_quality_score,
            local_quality_ready=local_quality_ready,
            adaptive_local_quality_score=adaptive_local_quality_score,
            adaptive_local_threshold=adaptive_local_threshold,
            action_task=action_task,
            codex_action_label=codex_action.action_label,
            codex_action_readiness=codex_action_readiness,
            action_specific_readiness=action_specific_readiness,
            action_specific_threshold=action_specific_threshold,
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
            adaptive_local_quality_score=adaptive_local_quality_score,
            adaptive_local_threshold=adaptive_local_threshold,
            action_task=action_task,
            codex_action_label=codex_action.action_label,
            codex_action_readiness=codex_action_readiness,
            action_specific_readiness=action_specific_readiness,
            action_specific_threshold=action_specific_threshold,
        )

    reasons.append("defaulting to cloud-first for moderate certainty")
    return RoutingDecision(
        mode=config.get("default_mode", "cloud"),
        reasons=reasons,
        similarity_score=similarity_score,
        task_complexity=complexity,
        local_quality_score=local_quality_score,
        local_quality_ready=local_quality_ready,
        adaptive_local_quality_score=adaptive_local_quality_score,
        adaptive_local_threshold=adaptive_local_threshold,
        action_task=action_task,
        codex_action_label=codex_action.action_label,
        codex_action_readiness=codex_action_readiness,
        action_specific_readiness=action_specific_readiness,
        action_specific_threshold=action_specific_threshold,
    )
