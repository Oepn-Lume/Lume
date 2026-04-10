"""Codex-oriented action taxonomy for on-site software work."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodexActionDecision:
    action_label: str
    action_family: str
    short_action: bool


ACTION_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("continue_task", "execution", ("continue", "缁х画", "resume", "go on")),
    ("inspect_log", "inspection", ("log", "stderr", "stdout", "error", "traceback", "stack trace")),
    ("prepare_patch", "patching", ("patch", "fix", "implement", "repair", "modify", "edit", "refactor", "修复", "实现")),
    ("publish_release", "delivery", ("publish", "release", "ship", "deploy", "push", "merge", "发布", "部署")),
    ("summarize_status", "status", ("summary", "summarize", "status", "report", "progress", "总结", "进展", "状态")),
    ("explain_why", "analysis", ("why", "原因", "为什么", "how come")),
]


def classify_codex_action(text: str) -> CodexActionDecision:
    lowered = str(text).strip().lower()
    tokens = [token.strip(".,:;!?()[]{}") for token in lowered.split() if token.strip()]
    short_action = len(tokens) <= 5
    for action_label, action_family, keywords in ACTION_RULES:
        if any(keyword in lowered for keyword in keywords):
            return CodexActionDecision(
                action_label=action_label,
                action_family=action_family,
                short_action=short_action,
            )
    return CodexActionDecision(
        action_label="generic_action",
        action_family="generic",
        short_action=short_action,
    )
