"""Start continuous shadow logging from local Codex sessions."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=0)
    parser.add_argument(
        "--sessions-root",
        default=r"C:\Users\yh-PC-003\.codex\sessions",
    )
    parser.add_argument(
        "--archived-root",
        default=r"C:\Users\yh-PC-003\.codex\archived_sessions",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = [
        sys.executable,
        str(ROOT / "scripts" / "watch_codex_training_data.py"),
        "--interval-seconds",
        str(args.interval_seconds),
        "--sessions-root",
        args.sessions_root,
        "--archived-root",
        args.archived_root,
    ]
    if args.iterations:
        command.extend(["--iterations", str(args.iterations)])
    raise SystemExit(subprocess.run(command, cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
