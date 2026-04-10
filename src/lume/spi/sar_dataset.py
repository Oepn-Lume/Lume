"""Build State-Action-Reward protocol datasets from task runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .protocol import (
    SAR_PROTOCOL_VERSION,
    ActionEnvelope,
    ActionType,
    AgentType,
    DomainType,
    RewardEnvelope,
    SARRecord,
    StateEnvelope,
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _truncate_text(text: str, limit: int = 240) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _classify_agent_type(task_payload: dict[str, Any]) -> str:
    route_mode = str(task_payload.get("route_mode", "")).lower()
    if route_mode in {"local", "hybrid", "cloud"}:
        return AgentType.SOFTWARE_AGENT.value
    return AgentType.GENERIC_AGENT.value


def _classify_domain(task_payload: dict[str, Any]) -> str:
    route_mode = str(task_payload.get("route_mode", "")).lower()
    if route_mode in {"local", "hybrid", "cloud"}:
        return DomainType.SOFTWARE.value
    return DomainType.GENERIC.value


def _classify_action_type(tool_name: str | None) -> str:
    normalized = str(tool_name or "").strip().lower()
    if not normalized:
        return ActionType.DELIVER_RESULT.value
    if "patch" in normalized:
        return ActionType.PATCH_APPLY.value
    if "command" in normalized or "shell" in normalized or normalized in {"exec", "exec_command"}:
        return ActionType.SHELL_COMMAND.value
    if "route" in normalized:
        return ActionType.ROUTE_DECISION.value
    return ActionType.FUNCTION_CALL.value


def _derive_reward(task_payload: dict[str, Any], tool_trace: dict[str, Any]) -> RewardEnvelope:
    value_score = float(task_payload.get("value_score", 0.0) or 0.0)
    success = str(task_payload.get("result_status", "")).lower() == "completed"
    tool_call_count = len(tool_trace.get("tool_calls", []))
    reward_env = 1.0 if success else 0.0
    reward_align = min(1.0, value_score)
    reward_short = max(0.0, 1.0 - min(tool_call_count / 10.0, 1.0))
    energy_penalty = round(min(tool_call_count * 0.03, 0.3), 3)
    total_reward = round((0.45 * reward_env) + (0.4 * reward_align) + (0.15 * reward_short) - energy_penalty, 4)
    return RewardEnvelope(
        total_reward=total_reward,
        reward_align=round(reward_align, 4),
        reward_env=round(reward_env, 4),
        reward_short=round(reward_short, 4),
        energy_penalty=energy_penalty,
        success=success,
        metadata={"tool_call_count": tool_call_count},
    )


def build_sar_protocol_dataset(task_runs_root: Path, datasets_root: Path) -> Path:
    """Build a standardized SAR dataset from shadow task runs."""

    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "sar_protocol.jsonl"
    records: list[dict[str, Any]] = []

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        task_payload = _read_json(task_json)
        tool_trace = _read_json(task_dir / "tool_trace.json") if (task_dir / "tool_trace.json").exists() else {}
        file_changes = _read_json(task_dir / "file_changes.json") if (task_dir / "file_changes.json").exists() else {}
        outcome = _read_json(task_dir / "outcome.json") if (task_dir / "outcome.json").exists() else {}
        routing_metadata = dict(task_payload.get("metadata", {}))

        state = StateEnvelope(
            domain=_classify_domain(task_payload),
            world_snapshot={
                "task_id": task_payload.get("task_id"),
                "route_mode": task_payload.get("route_mode"),
                "model_used": task_payload.get("model_used"),
                "files_changed": [
                    change.get("path")
                    for change in file_changes.get("file_changes", [])
                    if isinstance(change, dict) and change.get("path")
                ],
                "output_source": task_payload.get("output_source"),
            },
            intent_trajectory=[
                {
                    "user_goal": task_payload.get("user_goal", ""),
                    "routing_reasons": routing_metadata.get("routing_reasons", []),
                    "planning_strategy": routing_metadata.get("planning_strategy"),
                }
            ],
            feedback_signals={
                "result_status": task_payload.get("result_status"),
                "value_score": task_payload.get("value_score", 0.0),
                "message_count": task_payload.get("message_count", 0),
                "tool_call_count": task_payload.get("tool_call_count", 0),
                "file_change_count": task_payload.get("file_change_count", 0),
            },
            metadata={
                "task_dir": str(task_dir),
                "cloud_simulated": routing_metadata.get("cloud_simulated", False),
            },
        )

        first_tool = None
        for tool_call in tool_trace.get("tool_calls", []):
            if isinstance(tool_call, dict) and tool_call.get("tool"):
                first_tool = tool_call
                break
        action = ActionEnvelope(
            action_type=_classify_action_type(first_tool.get("tool") if first_tool else None),
            action_payload={
                "tool_name": first_tool.get("tool") if first_tool else None,
                "summary": _truncate_text(first_tool.get("output_summary", "")) if first_tool else "deliver task output",
                "arguments": first_tool.get("arguments", {}) if first_tool else {},
                "files_changed": state.world_snapshot["files_changed"],
            },
            confidence=first_tool.get("arguments", {}).get("confidence") if first_tool else None,
            executor=str(first_tool.get("source", "codex")) if first_tool else "codex",
            metadata={"result_status": outcome.get("result_status", task_payload.get("result_status"))},
        )
        reward = _derive_reward(task_payload, tool_trace)

        records.append(
            SARRecord(
                record_id=f"{task_payload.get('task_id')}-sar",
                agent_type=_classify_agent_type(task_payload),
                state=state,
                action=action,
                reward=reward,
                protocol_version=SAR_PROTOCOL_VERSION,
                metadata={
                    "source": "shadow_task_run",
                    "protocol": SAR_PROTOCOL_VERSION,
                    "timestamp": task_payload.get("timestamp"),
                },
            ).to_dict()
        )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
