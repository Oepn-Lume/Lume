"""Foundational protocol objects for the Digital Sun expert exchange layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ExpertWeightShare:
    """A privacy-preserving summary of an expert battery update."""

    expert_name: str
    domain: str
    source_node: str
    quality_score: float
    reward_score: float
    adapter_path: str | None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["share_id"] = hashlib.sha1(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return payload


def build_weight_share_manifest(
    *,
    output_path: Path,
    expert_name: str,
    domain: str,
    source_node: str,
    quality_score: float,
    reward_score: float,
    adapter_path: str | None,
    notes: str = "",
) -> Path:
    """Write a local share manifest for later federated synchronization."""
    manifest = ExpertWeightShare(
        expert_name=expert_name,
        domain=domain,
        source_node=source_node,
        quality_score=quality_score,
        reward_score=reward_score,
        adapter_path=adapter_path,
        notes=notes,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest.to_dict(), indent=2), "utf-8")
    return output_path
