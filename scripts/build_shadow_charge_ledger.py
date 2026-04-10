"""Build an append-only ledger of daytime shadow assets for night charging."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.charging import build_shadow_charge_ledger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "shadow_charge"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written_paths = build_shadow_charge_ledger(
        Path(args.task_runs_root),
        Path(args.output_root),
    )
    for path in written_paths:
        print(path)


if __name__ == "__main__":
    main()
