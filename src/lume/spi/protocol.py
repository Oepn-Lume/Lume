"""State-Action-Reward protocol types for Battery Model 2.0."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StateEnvelope:
    """Standardized state input for local battery evolution."""

    domain: str
    world_snapshot: dict[str, Any]
    intent_trajectory: list[dict[str, Any]]
    feedback_signals: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

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
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_type": self.agent_type,
            "state": self.state.to_dict(),
            "action": self.action.to_dict(),
            "reward": self.reward.to_dict(),
            "metadata": self.metadata,
        }
