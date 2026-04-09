"""Continuously watch Codex session logs and refresh training data."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import build_distill_datasets
from lume.logging import import_codex_sessions_incremental


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sessions-root",
        default=r"C:\Users\yh-PC-003\.codex\sessions",
    )
    parser.add_argument(
        "--archived-root",
        default=r"C:\Users\yh-PC-003\.codex\archived_sessions",
    )
    parser.add_argument(
        "--raw-output",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import.jsonl"),
    )
    parser.add_argument(
        "--state",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import-state.json"),
    )
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--raw-logs-root",
        default=str(ROOT / "data" / "raw_logs"),
    )
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    iteration = 0
    while True:
        iteration += 1
        result = import_codex_sessions_incremental(
            Path(args.sessions_root),
            Path(args.raw_output),
            Path(args.state),
            archived_root=Path(args.archived_root),
        )
        if result["imported_records"] > 0:
            build_distill_datasets(
                Path(args.task_runs_root),
                Path(args.datasets_root),
                Path(args.raw_logs_root),
            )
        print(
            f"iteration={iteration} scanned_files={result['scanned_files']} "
            f"imported_records={result['imported_records']}"
        )
        if args.iterations and iteration >= args.iterations:
            break
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
