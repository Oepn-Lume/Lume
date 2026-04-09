"""Build, report, train, and evaluate the minimal Lume RLEF cycle."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--max-preference-samples", type=int)
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "transformers-dpo-v1"),
    )
    return parser.parse_args()


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, check=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()
    python_exe = sys.executable
    _run([python_exe, str(ROOT / "scripts" / "build_distill_dataset.py")])
    _run([python_exe, str(ROOT / "scripts" / "build_rlef_report.py")])
    train_command = [
        python_exe,
        str(ROOT / "scripts" / "train_rlef_dpo.py"),
        "--device",
        args.device,
        "--output-root",
        args.output_root,
    ]
    if args.max_preference_samples is not None:
        train_command.extend(["--max-samples", str(args.max_preference_samples)])
    _run(train_command)
    _run(
        [
            python_exe,
            str(ROOT / "scripts" / "evaluate_rlef_preference.py"),
            "--model-root",
            args.output_root,
            "--device",
            args.device,
        ]
    )


if __name__ == "__main__":
    main()
