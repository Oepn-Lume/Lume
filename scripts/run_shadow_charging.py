"""Run the night-side charging loop after checking idle and power conditions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.charging import detect_device_state, evaluate_charging_window


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--idle-minutes", type=int)
    parser.add_argument("--cpu-percent", type=float)
    parser.add_argument("--hour", type=int)
    parser.add_argument("--is-charging", action="store_true")
    parser.add_argument("--gpu-busy", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-sync", action="store_true")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--quality-max-examples", type=int, default=8)
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--ledger-root",
        default=str(ROOT / "data" / "distilled" / "shadow_charge"),
    )
    parser.add_argument(
        "--report-root",
        default=str(ROOT / "data" / "distilled" / "shadow_charge" / "nightly_runs"),
    )
    return parser.parse_args()


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)


def _extract_paths(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    python_exe = sys.executable
    detected = detect_device_state(
        hour_override=args.hour,
        idle_minutes_override=args.idle_minutes,
        is_charging_override=True if args.is_charging else None,
        cpu_percent_override=args.cpu_percent,
        gpu_busy_override=True if args.gpu_busy else None,
    )
    state = detected.state
    decision = evaluate_charging_window(state)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_root = Path(args.report_root) / f"night-charge-{run_id}"
    report_root.mkdir(parents=True, exist_ok=True)
    report_json = report_root / "shadow_charging_report.json"
    report_md = report_root / "shadow_charging_report.md"

    payload: dict[str, object] = {
        "run_id": run_id,
        "device_state": {
            "hour": state.hour,
            "idle_minutes": state.idle_minutes,
            "is_charging": state.is_charging,
            "cpu_percent": state.cpu_percent,
            "gpu_busy": state.gpu_busy,
        },
        "detection_source": detected.detection_source,
        "decision": {
            "should_charge": decision.should_charge,
            "charging_window_active": decision.charging_window_active,
            "reasons": decision.reasons,
            "forced": args.force,
        },
        "steps": [],
    }

    if not decision.should_charge and not args.force:
        report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
        report_md.write_text(
            "\n".join(
                [
                    "# Shadow Charging Report",
                    "",
                    f"- Run ID: `{run_id}`",
                    "- Result: `skipped`",
                    f"- Device State: hour={state.hour}, idle={state.idle_minutes}m, charging={state.is_charging}, cpu={state.cpu_percent}",
                    f"- Reasons: `{', '.join(decision.reasons)}`",
                    "",
                ]
            ),
            "utf-8",
        )
        print(report_json)
        print(report_md)
        return

    ledger_command = [
        python_exe,
        str(ROOT / "scripts" / "build_shadow_charge_ledger.py"),
        "--task-runs-root",
        args.task_runs_root,
        "--output-root",
        args.ledger_root,
    ]
    ledger_result = _run(ledger_command)
    payload["steps"].append(
        {
            "step": "build_shadow_charge_ledger",
            "command": ledger_command,
            "paths": _extract_paths(ledger_result.stdout),
        }
    )

    cycle_command = [
        python_exe,
        str(ROOT / "scripts" / "run_continuous_cycle.py"),
        "--device",
        args.device,
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--quality-max-examples",
        str(args.quality_max_examples),
    ]
    if args.skip_sync:
        cycle_command.append("--skip-sync")
    if args.max_samples is not None:
        cycle_command.extend(["--max-samples", str(args.max_samples)])
    cycle_result = _run(cycle_command)
    payload["steps"].append(
        {
            "step": "run_continuous_cycle",
            "command": cycle_command,
            "paths": _extract_paths(cycle_result.stdout),
        }
    )

    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    report_md.write_text(
        "\n".join(
            [
                "# Shadow Charging Report",
                "",
                f"- Run ID: `{run_id}`",
                "- Result: `completed`",
                f"- Device State: hour={state.hour}, idle={state.idle_minutes}m, charging={state.is_charging}, cpu={state.cpu_percent}",
                f"- Reasons: `{', '.join(decision.reasons)}`",
                "",
                "## Steps",
                *[f"- `{step['step']}`" for step in payload["steps"]],
                "",
            ]
        ),
        "utf-8",
    )
    print(report_json)
    print(report_md)


if __name__ == "__main__":
    main()
