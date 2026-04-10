"""Policy helpers for deciding when the Battery Model may train."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceState:
    """Observed local device state used for shadow-charging decisions."""

    hour: int
    idle_minutes: int
    is_charging: bool
    cpu_percent: float = 0.0
    gpu_busy: bool = False


@dataclass(slots=True)
class ChargingDecision:
    """Result of evaluating whether night charging may begin."""

    should_charge: bool
    reasons: list[str]
    charging_window_active: bool


def _in_charging_window(hour: int, *, start_hour: int = 23, end_hour: int = 6) -> bool:
    if start_hour == end_hour:
        return True
    if start_hour < end_hour:
        return start_hour <= hour < end_hour
    return hour >= start_hour or hour < end_hour


def evaluate_charging_window(
    state: DeviceState,
    *,
    min_idle_minutes: int = 30,
    max_cpu_percent: float = 35.0,
    start_hour: int = 23,
    end_hour: int = 6,
) -> ChargingDecision:
    """Evaluate whether the device should enter shadow-charging mode."""

    reasons: list[str] = []
    charging_window_active = _in_charging_window(
        state.hour,
        start_hour=start_hour,
        end_hour=end_hour,
    )

    if not charging_window_active:
        reasons.append("outside charging window")
    if state.idle_minutes < min_idle_minutes:
        reasons.append("user not idle long enough")
    if not state.is_charging:
        reasons.append("device not charging")
    if state.cpu_percent > max_cpu_percent:
        reasons.append("cpu usage too high")
    if state.gpu_busy:
        reasons.append("gpu already busy")

    return ChargingDecision(
        should_charge=not reasons,
        reasons=reasons or ["charging conditions satisfied"],
        charging_window_active=charging_window_active,
    )
