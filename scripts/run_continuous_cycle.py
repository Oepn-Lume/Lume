"""Run a full Lume continuous retraining cycle."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--quality-max-examples", type=int, default=8)
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--raw-logs-root",
        default=str(ROOT / "data" / "raw_logs"),
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-cycle"),
    )
    parser.add_argument(
        "--quality-output",
        default=str(ROOT / "configs" / "local_quality.json"),
    )
    parser.add_argument(
        "--quality-history-output",
        default=str(ROOT / "data" / "distilled" / "local_quality_history.jsonl"),
    )
    parser.add_argument(
        "--report-root",
        default=str(ROOT / "data" / "distilled" / "cycles"),
    )
    parser.add_argument(
        "--route-task",
        default="write a short summary",
        help="Representative task used to verify router feedback after retraining.",
    )
    parser.add_argument("--skip-sync", action="store_true")
    return parser.parse_args()


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def _extract_existing_paths(stdout: str) -> list[str]:
    paths: list[str] = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":\\" in line or line.startswith("/"):
            paths.append(line)
    return paths


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def main() -> None:
    args = parse_args()
    python_exe = sys.executable
    cycle_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_root = Path(args.report_root) / f"cycle-{cycle_timestamp}"
    report_root.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, Any]] = []

    if not args.skip_sync:
        sync_command = [
            python_exe,
            str(ROOT / "scripts" / "sync_codex_training_data.py"),
            "--device",
            args.device,
            "--skip-train",
        ]
        sync_result = _run(sync_command)
        steps.append(
            {
                "step": "sync",
                "command": sync_command,
                "stdout": sync_result.stdout,
                "paths": _extract_existing_paths(sync_result.stdout),
            }
        )

    build_command = [
        python_exe,
        str(ROOT / "scripts" / "build_distill_dataset.py"),
        "--task-runs-root",
        args.task_runs_root,
        "--datasets-root",
        args.datasets_root,
        "--raw-logs-root",
        args.raw_logs_root,
    ]
    build_result = _run(build_command)
    steps.append(
        {
            "step": "build_datasets",
            "command": build_command,
            "stdout": build_result.stdout,
            "paths": _extract_existing_paths(build_result.stdout),
        }
    )

    train_command = [
        python_exe,
        str(ROOT / "scripts" / "train_lora.py"),
        "--datasets-root",
        args.datasets_root,
        "--output-root",
        args.output_root,
        "--device",
        args.device,
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--quality-output",
        args.quality_output,
        "--quality-history-output",
        args.quality_history_output,
        "--quality-max-examples",
        str(args.quality_max_examples),
    ]
    if args.max_samples is not None:
        train_command.extend(["--max-samples", str(args.max_samples)])
    train_result = _run(train_command)
    steps.append(
        {
            "step": "train",
            "command": train_command,
            "stdout": train_result.stdout,
            "paths": _extract_existing_paths(train_result.stdout),
        }
    )

    eval_json = report_root / "evaluation_report.json"
    eval_md = report_root / "evaluation_report.md"
    eval_command = [
        python_exe,
        str(ROOT / "scripts" / "evaluate_local_model.py"),
        "--model-root",
        args.output_root,
        "--datasets-root",
        args.datasets_root,
        "--max-examples",
        str(args.quality_max_examples),
        "--device",
        args.device,
        "--output-json",
        str(eval_json),
        "--output-md",
        str(eval_md),
    ]
    eval_result = _run(eval_command)
    steps.append(
        {
            "step": "evaluate",
            "command": eval_command,
            "stdout": eval_result.stdout,
            "paths": [str(eval_json), str(eval_md)],
        }
    )

    route_command = [
        python_exe,
        str(ROOT / "scripts" / "route_task.py"),
        "--task",
        args.route_task,
        "--task-runs-root",
        args.task_runs_root,
        "--local-quality-config",
        args.quality_output,
    ]
    route_result = _run(route_command)
    route_payload = json.loads(route_result.stdout)
    route_report_path = report_root / "route_decision.json"
    route_report_path.write_text(json.dumps(route_payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    steps.append(
        {
            "step": "route_feedback",
            "command": route_command,
            "stdout": route_result.stdout,
            "paths": [str(route_report_path)],
        }
    )

    quality_payload = _load_json(Path(args.quality_output))
    evaluation_payload = _load_json(eval_json)
    training_metrics = _load_json(Path(args.output_root) / "metrics.json")

    report_payload = {
        "cycle_timestamp": cycle_timestamp,
        "model_root": str(Path(args.output_root)),
        "quality_output": str(Path(args.quality_output)),
        "quality_history_output": str(Path(args.quality_history_output)),
        "route_task": args.route_task,
        "quality_snapshot": quality_payload,
        "training_metrics": training_metrics,
        "evaluation_summary": evaluation_payload,
        "route_feedback": route_payload,
        "steps": steps,
    }
    report_json = report_root / "cycle_report.json"
    report_md = report_root / "cycle_report.md"
    report_json.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", "utf-8")

    report_lines = [
        "# Lume Continuous Retraining Cycle",
        "",
        f"- Timestamp: `{cycle_timestamp}`",
        f"- Model Root: `{Path(args.output_root)}`",
        f"- Route Check Task: `{args.route_task}`",
        f"- Local Quality Score: `{quality_payload.get('local_quality_score', 'n/a')}`",
        f"- Final Loss: `{training_metrics.get('final_loss', 'n/a')}`",
        f"- Training Perplexity: `{training_metrics.get('perplexity', 'n/a')}`",
        f"- Route Decision: `{route_payload.get('decision', {}).get('mode', 'n/a')}`",
        "",
        "## Artifacts",
        "",
        f"- Evaluation JSON: `{eval_json}`",
        f"- Evaluation Markdown: `{eval_md}`",
        f"- Route Decision: `{route_report_path}`",
        f"- Quality Snapshot: `{Path(args.quality_output)}`",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        report_lines.append(f"- `{step['step']}`")
    report_md.write_text("\n".join(report_lines) + "\n", "utf-8")

    print(report_json)
    print(report_md)
    print(route_report_path)


if __name__ == "__main__":
    main()
