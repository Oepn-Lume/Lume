"""Generate distillation datasets from task runs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import build_distill_datasets
from lume.rl import build_rlef_datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written_paths = build_distill_datasets(
        Path(args.task_runs_root),
        Path(args.datasets_root),
        Path(args.raw_logs_root),
    )
    written_paths.extend(
        build_rlef_datasets(
            Path(args.task_runs_root),
            Path(args.datasets_root),
        )
    )
    for path in written_paths:
        print(path)


if __name__ == "__main__":
    main()
