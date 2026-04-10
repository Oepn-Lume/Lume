"""State-Action-Reward protocol types for Battery Model 2.0."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


SAR_PROTOCOL_VERSION = "sar-v1"


class DomainType(StrEnum):
    SOFTWARE = "software"
    ROBOTICS = "robotics"
    DRONE = "drone"
    VOICE = "voice"
    IOT = "iot"
    GENERIC = "generic"


class AgentType(StrEnum):
    SOFTWARE_AGENT = "software-agent"
    ROBOT_AGENT = "robot-agent"
    DRONE_AGENT = "drone-agent"
    VOICE_AGENT = "voice-agent"
    IOT_AGENT = "iot-agent"
    GENERIC_AGENT = "generic-agent"


class ActionType(StrEnum):
    DELIVER_RESULT = "deliver_result"
    FUNCTION_CALL = "function_call"
    PATCH_APPLY = "patch_apply"
    SHELL_COMMAND = "shell_command"
    ROUTE_DECISION = "route_decision"
    SENSOR_COMMAND = "sensor_command"
    MOTION_COMMAND = "motion_command"
    STATE_UPDATE = "state_update"


def _ensure_mapping(name: str, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dict, got {type(value).__name__}")
    return value


def _ensure_sequence(name: str, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a list, got {type(value).__name__}")
    return value


@dataclass(slots=True)
class StateEnvelope:
    """Standardized state input for local battery evolution."""

    domain: str
    world_snapshot: dict[str, Any]
    intent_trajectory: list[dict[str, Any]]
    feedback_signals: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.domain = DomainType(self.domain).value
        self.world_snapshot = _ensure_mapping("world_snapshot", self.world_snapshot)
        self.intent_trajectory = _ensure_sequence("intent_trajectory", self.intent_trajectory)
        self.feedback_signals = _ensure_mapping("feedback_signals", self.feedback_signals)
        self.metadata = _ensure_mapping("metadata", self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionEnvelope:
    """Standardized action output for local or cloud execution."""

    action_type: str
    action_payload: dict[str, Any]
    confidence: float | None = None
    executor: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.action_type = ActionType(self.action_type).value
        self.action_payload = _ensure_mapping("action_payload", self.action_payload)
        self.metadata = _ensure_mapping("metadata", self.metadata)
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RewardEnvelope:
    """Standardized reward signal derived from engineering feedback."""

    total_reward: float
    reward_align: float = 0.0
    reward_env: float = 0.0
    reward_short: float = 0.0
    energy_penalty: float = 0.0
    success: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.metadata = _ensure_mapping("metadata", self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SARRecord:
    """A complete State-Action-Reward record for cross-domain battery training."""

    record_id: str
    agent_type: str
    state: StateEnvelope
    action: ActionEnvelope
    reward: RewardEnvelope
    protocol_version: str = SAR_PROTOCOL_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.agent_type = AgentType(self.agent_type).value
        self.metadata = _ensure_mapping("metadata", self.metadata)
        if self.protocol_version != SAR_PROTOCOL_VERSION:
            raise ValueError(
                f"unsupported protocol_version={self.protocol_version!r}; expected {SAR_PROTOCOL_VERSION!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "record_id": self.record_id,
            "agent_type": self.agent_type,
            "state": self.state.to_dict(),
            "action": self.action.to_dict(),
            "reward": self.reward.to_dict(),
            "metadata": self.metadata,
        }
