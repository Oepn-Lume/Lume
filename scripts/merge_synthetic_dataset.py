"""Merge generated synthetic corpus into the main Lume datasets directory."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import merge_synthetic_corpus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-root",
        default=str(ROOT / "data" / "generated_corpus"),
    )
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = merge_synthetic_corpus(
        Path(args.generated_root),
        Path(args.datasets_root),
    )
    print(path)


if __name__ == "__main__":
    main()
