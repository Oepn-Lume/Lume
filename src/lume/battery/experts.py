"""Expert battery profiles for the Digital Sun battery matrix."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    current_entry: dict[str, Any] | None = None
    current_list_key: str | None = None

    for raw_line in path.read_text("utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                data[key] = value
                current_section = None
                current_entry = None
                current_list_key = None
            else:
                data[key] = []
                current_section = key
                current_entry = None
                current_list_key = None
            continue

        if current_section and indent == 2 and stripped.startswith("- "):
            item_content = stripped[2:]
            entry: dict[str, Any] = {}
            if item_content and ":" in item_content:
                key, value = item_content.split(":", 1)
                entry[key.strip()] = value.strip().strip('"')
            data[current_section].append(entry)
            current_entry = entry
            current_list_key = None
            continue

        if current_entry is not None and indent >= 4:
            if stripped.endswith(":") and ":" not in stripped[:-1]:
                current_list_key = stripped[:-1].strip()
                current_entry[current_list_key] = []
                continue
            if stripped.startswith("- ") and current_list_key:
                current_entry[current_list_key].append(stripped[2:].strip().strip('"'))
                continue
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current_entry[key.strip()] = value.strip().strip('"')
                current_list_key = None

    return data


@dataclass(slots=True)
class ExpertProfile:
    """A single edge expert in the battery matrix."""

    name: str
    domain: str
    description: str
    model: str
    adapter: str | None
    privacy_sensitive: bool
    keywords: list[str]
    confidence_bias: float = 0.0


def load_expert_profiles(config_path: Path) -> list[ExpertProfile]:
    """Load expert battery profiles from a small YAML config."""
    payload = _parse_simple_yaml(config_path)
    experts: list[ExpertProfile] = []
    for item in payload.get("experts", []):
        experts.append(
            ExpertProfile(
                name=str(item.get("name", "unknown")),
                domain=str(item.get("domain", "general")),
                description=str(item.get("description", "")),
                model=str(item.get("model", "gemma4:31b")),
                adapter=str(item.get("adapter", "")) or None,
                privacy_sensitive=str(item.get("privacy_sensitive", "false")).lower() == "true",
                keywords=[str(keyword).lower() for keyword in item.get("keywords", [])],
                confidence_bias=float(item.get("confidence_bias", 0.0) or 0.0),
            )
        )
    return experts
