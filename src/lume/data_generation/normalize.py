"""Normalization, deduplication, and output helpers for generated samples."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .schema import GeneratedSample


def deduplicate_samples(samples: list[GeneratedSample]) -> list[GeneratedSample]:
    seen: set[str] = set()
    deduped: list[GeneratedSample] = []
    for sample in samples:
        key = hashlib.sha1(
            f"{sample.input}\n---\n{sample.target}".encode("utf-8")
        ).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sample)
    return deduped


def filter_samples(samples: list[GeneratedSample], min_quality: float) -> list[GeneratedSample]:
    return [sample for sample in samples if sample.accepted and sample.quality_score >= min_quality]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
