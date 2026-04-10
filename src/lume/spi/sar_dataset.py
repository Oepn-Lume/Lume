"""Build State-Action-Reward protocol datasets from task runs."""

from __future__ import annotations

from pathlib import Path

import json

from .adapters import build_default_sar_registry


def build_sar_protocol_dataset(task_runs_root: Path, datasets_root: Path) -> Path:
    """Build a standardized SAR dataset from shadow task runs."""

    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "sar_protocol.jsonl"
    records: list[dict[str, object]] = []
    registry = build_default_sar_registry()

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        task_payload = json.loads(task_json.read_text("utf-8"))
        adapter = registry.resolve(task_payload, task_dir)
        if adapter is None:
            continue
        records.append(adapter.build_record(task_payload, task_dir).to_dict())

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
