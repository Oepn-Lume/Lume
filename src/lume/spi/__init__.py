"""Standardized battery protocol interfaces."""

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
from .adapters import (
    RoboticsTraceAdapter,
    SARAdapterRegistry,
    SoftwareTaskRunAdapter,
    build_default_sar_registry,
)
from .sar_dataset import build_sar_protocol_dataset

__all__ = [
    "SAR_PROTOCOL_VERSION",
    "ActionEnvelope",
    "ActionType",
    "AgentType",
    "DomainType",
    "RewardEnvelope",
    "SARRecord",
    "RoboticsTraceAdapter",
    "SARAdapterRegistry",
    "SoftwareTaskRunAdapter",
    "StateEnvelope",
    "build_default_sar_registry",
    "build_sar_protocol_dataset",
]
