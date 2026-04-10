"""Build V4-ready training datasets with stronger continue/action representation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import build_battery_state_dataset, build_continue_state_sft_dataset
from lume.distill.codex_actions import build_codex_action_dataset
from lume.distill.train import DEFAULT_DATASET_FILES


REBALANCE_MULTIPLIERS = {
    "codex_action_sft.jsonl": 3,
    "battery_state_sft.jsonl": 3,
    "continue_state_sft.jsonl": 4,
    "developer_chain_sft.jsonl": 2,
    "historical_workspace_code_sft.jsonl": 2,
    "hybrid_refinement_sft.jsonl": 2,
}

SUPPLEMENTAL_FILES = [
    "codex_action_eval.jsonl",
    "codex_continue_eval.jsonl",
    "codex_patch_eval.jsonl",
    "codex_log_eval.jsonl",
    "continue_alignment_dpo.jsonl",
    "continue_alignment_grpo.jsonl",
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
        "utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-root", default=str(ROOT / "data" / "reports"))
    parser.add_argument("--source-datasets-root", default=str(ROOT / "data" / "datasets"))
    parser.add_argument("--task-runs-root", default=str(ROOT / "data" / "task_runs"))
    parser.add_argument("--output-root", default=str(ROOT / "data" / "datasets_v4"))
    parser.add_argument("--report-output", default=str(ROOT / "data" / "reports" / "v4_dataset_report.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reports_root = Path(args.reports_root)
    source_datasets_root = Path(args.source_datasets_root)
    task_runs_root = Path(args.task_runs_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    build_codex_action_dataset(reports_root, source_datasets_root)
    continue_state_path = build_continue_state_sft_dataset(
        task_runs_root,
        source_datasets_root / "continue_state_sft.jsonl",
    )
    battery_state_path = build_battery_state_dataset(
        task_runs_root,
        source_datasets_root,
    )

    summary: dict[str, Any] = {
        "source_datasets_root": str(source_datasets_root),
        "output_root": str(output_root),
        "copied_files": [],
        "rebalanced_files": {},
        "continue_state_dataset": str(continue_state_path),
        "battery_state_dataset": str(battery_state_path),
    }

    for filename in DEFAULT_DATASET_FILES:
        source_path = source_datasets_root / filename
        output_path = output_root / filename
        if not source_path.exists():
            continue
        multiplier = REBALANCE_MULTIPLIERS.get(filename, 1)
        records = _read_jsonl(source_path)
        if records and multiplier > 1:
            expanded: list[dict[str, Any]] = []
            for index in range(multiplier):
                for record in records:
                    clone = dict(record)
                    metadata = clone.get("metadata", {})
                    metadata = dict(metadata) if isinstance(metadata, dict) else {}
                    metadata["v4_rebalance_repeat"] = index + 1
                    metadata["v4_rebalance_source_file"] = filename
                    clone["metadata"] = metadata
                    expanded.append(clone)
            _write_jsonl(output_path, expanded)
            summary["rebalanced_files"][filename] = {
                "source_records": len(records),
                "output_records": len(expanded),
                "multiplier": multiplier,
            }
        else:
            shutil.copy2(source_path, output_path)
            summary["copied_files"].append(filename)

    for filename in SUPPLEMENTAL_FILES:
        source_path = source_datasets_root / filename
        output_path = output_root / filename
        if not source_path.exists():
            continue
        shutil.copy2(source_path, output_path)
        summary["copied_files"].append(filename)

    report_output = Path(args.report_output)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
