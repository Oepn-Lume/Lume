"""Build the standardized SAR protocol dataset from task runs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.spi import build_sar_protocol_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-runs-root", default=str(ROOT / "data" / "task_runs"))
    parser.add_argument("--datasets-root", default=str(ROOT / "data" / "datasets"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_sar_protocol_dataset(Path(args.task_runs_root), Path(args.datasets_root))
    print(path)


if __name__ == "__main__":
    main()
