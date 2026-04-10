"""Best-effort local device state detection for shadow charging."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
import platform
from typing import Any

from .policy import DeviceState


@dataclass(slots=True)
class DetectedDeviceState:
    """A device state paired with its data-source metadata."""

    state: DeviceState
    detection_source: dict[str, Any]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("Reserved1", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


def _detect_idle_minutes_windows() -> tuple[int | None, str]:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(last_input)):
        return None, "windows:last_input_failed"
    tick_ms = kernel32.GetTickCount64()
    idle_ms = max(0, int(tick_ms - last_input.dwTime))
    return idle_ms // 60000, "windows:last_input_info"


def _detect_charging_windows() -> tuple[bool | None, dict[str, Any]]:
    status = SYSTEM_POWER_STATUS()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        return None, {"source": "windows:power_status_failed"}
    ac_status = None if status.ACLineStatus == 255 else status.ACLineStatus
    is_charging = ac_status == 1
    return is_charging, {
        "source": "windows:power_status",
        "ac_line_status": ac_status,
        "battery_life_percent": None if status.BatteryLifePercent == 255 else int(status.BatteryLifePercent),
    }


def detect_device_state(
    *,
    hour_override: int | None = None,
    idle_minutes_override: int | None = None,
    is_charging_override: bool | None = None,
    cpu_percent_override: float | None = None,
    gpu_busy_override: bool | None = None,
) -> DetectedDeviceState:
    """Best-effort device state detection with optional manual overrides."""

    now = datetime.now()
    detection_source: dict[str, Any] = {
        "platform": platform.system(),
        "timestamp": now.isoformat(),
    }

    hour = hour_override if hour_override is not None else now.hour
    detection_source["hour_source"] = "override" if hour_override is not None else "local_clock"

    idle_minutes: int | None = idle_minutes_override
    if idle_minutes is None:
        if platform.system() == "Windows":
            idle_minutes, source = _detect_idle_minutes_windows()
            detection_source["idle_source"] = source
        else:
            detection_source["idle_source"] = "unsupported_platform"
    else:
        detection_source["idle_source"] = "override"

    is_charging: bool | None = is_charging_override
    if is_charging is None:
        if platform.system() == "Windows":
            detected, meta = _detect_charging_windows()
            is_charging = detected
            detection_source["power"] = meta
        else:
            detection_source["power"] = {"source": "unsupported_platform"}
    else:
        detection_source["power"] = {"source": "override"}

    cpu_percent = cpu_percent_override if cpu_percent_override is not None else 0.0
    detection_source["cpu_source"] = "override" if cpu_percent_override is not None else "default_zero"

    gpu_busy = gpu_busy_override if gpu_busy_override is not None else False
    detection_source["gpu_source"] = "override" if gpu_busy_override is not None else "default_false"

    state = DeviceState(
        hour=hour,
        idle_minutes=idle_minutes if idle_minutes is not None else 0,
        is_charging=bool(is_charging) if is_charging is not None else False,
        cpu_percent=float(cpu_percent),
        gpu_busy=bool(gpu_busy),
    )
    detection_source["fallbacks_used"] = {
        "idle_minutes": idle_minutes is None,
        "is_charging": is_charging is None,
    }
    return DetectedDeviceState(state=state, detection_source=detection_source)
