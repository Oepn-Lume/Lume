"""One-command launcher for the Lume Treasury prototype."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        nargs="?",
        default="shadow",
        choices=["shadow", "sync", "pipeline", "cycle"],
        help="Launch mode. Defaults to shadow.",
    )
    parser.add_argument("--task", help="Task text for pipeline mode.")
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--skip-train", action="store_true")
    return parser.parse_args()


def _run(command: list[str]) -> int:
    return subprocess.run(command, cwd=ROOT).returncode


def main() -> None:
    args = parse_args()
    python_exe = sys.executable

    if args.mode == "shadow":
        raise SystemExit(
            _run(
                [
                    python_exe,
                    str(ROOT / "scripts" / "start_shadow_logger.py"),
                    "--interval-seconds",
                    str(args.interval_seconds),
                    "--iterations",
                    str(args.iterations),
                ]
            )
        )

    if args.mode == "sync":
        command = [
            python_exe,
            str(ROOT / "scripts" / "sync_codex_training_data.py"),
            "--device",
            args.device,
        ]
        if args.skip_train:
            command.append("--skip-train")
        raise SystemExit(_run(command))

    if args.mode == "cycle":
        raise SystemExit(
            _run(
                [
                    python_exe,
                    str(ROOT / "scripts" / "run_continuous_cycle.py"),
                    "--device",
                    args.device,
                ]
            )
        )

    task = args.task or "write a short summary"
    raise SystemExit(
        _run(
            [
                python_exe,
                str(ROOT / "scripts" / "run_lume_pipeline.py"),
                "--task",
                task,
            ]
        )
    )


if __name__ == "__main__":
    main()
