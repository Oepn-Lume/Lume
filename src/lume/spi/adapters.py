"""Adapter registry for building SAR records from different agent domains."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol

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


class SARAdapter(Protocol):
    """Protocol for mapping a task directory into a SAR record."""

    name: str

    def supports(self, task_payload: dict[str, Any], task_dir: Path) -> bool: ...

    def build_record(self, task_payload: dict[str, Any], task_dir: Path) -> SARRecord: ...


@dataclass(slots=True)
class SoftwareTaskRunAdapter:
    """Default SAR adapter for Lume software task runs."""

    name: str = "software-task-run"

    def supports(self, task_payload: dict[str, Any], task_dir: Path) -> bool:
        route_mode = str(task_payload.get("route_mode", "")).lower()
        return route_mode in {"local", "hybrid", "cloud"} or (task_dir / "tool_trace.json").exists()

    def build_record(self, task_payload: dict[str, Any], task_dir: Path) -> SARRecord:
        tool_trace = _read_json(task_dir / "tool_trace.json") if (task_dir / "tool_trace.json").exists() else {}
        file_changes = _read_json(task_dir / "file_changes.json") if (task_dir / "file_changes.json").exists() else {}
        outcome = _read_json(task_dir / "outcome.json") if (task_dir / "outcome.json").exists() else {}
        routing_metadata = dict(task_payload.get("metadata", {}))

        state = StateEnvelope(
            domain=DomainType.SOFTWARE.value,
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

        value_score = float(task_payload.get("value_score", 0.0) or 0.0)
        success = str(task_payload.get("result_status", "")).lower() == "completed"
        tool_call_count = len(tool_trace.get("tool_calls", []))
        reward_env = 1.0 if success else 0.0
        reward_align = min(1.0, value_score)
        reward_short = max(0.0, 1.0 - min(tool_call_count / 10.0, 1.0))
        energy_penalty = round(min(tool_call_count * 0.03, 0.3), 3)
        total_reward = round((0.45 * reward_env) + (0.4 * reward_align) + (0.15 * reward_short) - energy_penalty, 4)
        reward = RewardEnvelope(
            total_reward=total_reward,
            reward_align=round(reward_align, 4),
            reward_env=round(reward_env, 4),
            reward_short=round(reward_short, 4),
            energy_penalty=energy_penalty,
            success=success,
            metadata={"tool_call_count": tool_call_count},
        )

        return SARRecord(
            record_id=f"{task_payload.get('task_id')}-sar",
            agent_type=AgentType.SOFTWARE_AGENT.value,
            state=state,
            action=action,
            reward=reward,
            protocol_version=SAR_PROTOCOL_VERSION,
            metadata={
                "source": "shadow_task_run",
                "protocol": SAR_PROTOCOL_VERSION,
                "timestamp": task_payload.get("timestamp"),
                "adapter": self.name,
            },
        )


@dataclass(slots=True)
class RoboticsTraceAdapter:
    """SAR adapter for robotics-style traces with motion feedback."""

    name: str = "robotics-trace"

    def supports(self, task_payload: dict[str, Any], task_dir: Path) -> bool:
        domain = str(task_payload.get("domain", "")).lower()
        agent_type = str(task_payload.get("agent_type", "")).lower()
        return (task_dir / "robot_trace.json").exists() or domain == "robotics" or agent_type == "robot-agent"

    def build_record(self, task_payload: dict[str, Any], task_dir: Path) -> SARRecord:
        robot_trace = _read_json(task_dir / "robot_trace.json") if (task_dir / "robot_trace.json").exists() else {}
        trace_steps = robot_trace.get("trace_steps", [])
        latest_step = trace_steps[-1] if trace_steps else {}
        motion_summary = robot_trace.get("motion_summary", {})

        state = StateEnvelope(
            domain=DomainType.ROBOTICS.value,
            world_snapshot={
                "task_id": task_payload.get("task_id"),
                "environment": robot_trace.get("environment", "unknown"),
                "pose": robot_trace.get("pose", {}),
                "sensors": robot_trace.get("sensors", {}),
                "active_goal": task_payload.get("user_goal", task_payload.get("goal", "")),
            },
            intent_trajectory=[
                {
                    "step_index": step.get("step_index"),
                    "intent": step.get("intent"),
                    "controller_mode": step.get("controller_mode"),
                }
                for step in trace_steps[-3:]
                if isinstance(step, dict)
            ],
            feedback_signals={
                "result_status": task_payload.get("result_status", robot_trace.get("result_status")),
                "path_efficiency": motion_summary.get("path_efficiency", 0.0),
                "collision_count": motion_summary.get("collision_count", 0),
                "energy_used": motion_summary.get("energy_used", 0.0),
                "latency_ms": motion_summary.get("latency_ms", 0.0),
            },
            metadata={
                "task_dir": str(task_dir),
                "adapter": self.name,
            },
        )

        action = ActionEnvelope(
            action_type=ActionType.MOTION_COMMAND.value,
            action_payload={
                "command": latest_step.get("action", robot_trace.get("final_action", "hold_position")),
                "target_pose": latest_step.get("target_pose", {}),
                "motion_summary": motion_summary,
            },
            confidence=float(latest_step.get("confidence", 0.75) or 0.75),
            executor=str(robot_trace.get("executor", "local-robot-agent")),
            metadata={"environment": robot_trace.get("environment", "unknown")},
        )

        success = str(task_payload.get("result_status", robot_trace.get("result_status", ""))).lower() == "completed"
        reward_env = 1.0 if success else 0.0
        reward_align = float(motion_summary.get("path_efficiency", 0.0) or 0.0)
        reward_short = max(0.0, 1.0 - min(float(motion_summary.get("latency_ms", 0.0) or 0.0) / 1000.0, 1.0))
        energy_penalty = round(min(float(motion_summary.get("energy_used", 0.0) or 0.0) / 100.0, 0.3), 3)
        total_reward = round((0.45 * reward_env) + (0.4 * reward_align) + (0.15 * reward_short) - energy_penalty, 4)
        reward = RewardEnvelope(
            total_reward=total_reward,
            reward_align=round(reward_align, 4),
            reward_env=round(reward_env, 4),
            reward_short=round(reward_short, 4),
            energy_penalty=energy_penalty,
            success=success,
            metadata={
                "collision_count": motion_summary.get("collision_count", 0),
                "energy_used": motion_summary.get("energy_used", 0.0),
            },
        )

        return SARRecord(
            record_id=f"{task_payload.get('task_id')}-sar",
            agent_type=AgentType.ROBOT_AGENT.value,
            state=state,
            action=action,
            reward=reward,
            protocol_version=SAR_PROTOCOL_VERSION,
            metadata={
                "source": "robot_trace",
                "protocol": SAR_PROTOCOL_VERSION,
                "timestamp": task_payload.get("timestamp"),
                "adapter": self.name,
            },
        )


class SARAdapterRegistry:
    """Registry for selecting SAR adapters by task payload and source directory."""

    def __init__(self) -> None:
        self._adapters: list[SARAdapter] = []

    def register(self, adapter: SARAdapter) -> None:
        self._adapters.append(adapter)

    def resolve(self, task_payload: dict[str, Any], task_dir: Path) -> SARAdapter | None:
        for adapter in self._adapters:
            if adapter.supports(task_payload, task_dir):
                return adapter
        return None

    @property
    def adapters(self) -> tuple[SARAdapter, ...]:
        return tuple(self._adapters)


def build_default_sar_registry() -> SARAdapterRegistry:
    registry = SARAdapterRegistry()
    registry.register(RoboticsTraceAdapter())
    registry.register(SoftwareTaskRunAdapter())
    return registry
