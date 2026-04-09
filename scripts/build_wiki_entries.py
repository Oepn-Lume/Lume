"""Build Lume wiki pages from shadow task logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.memory import build_wiki


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--wiki-root",
        default=str(ROOT / "data" / "wiki"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written_paths = build_wiki(
        Path(args.task_runs_root),
        Path(args.wiki_root),
    )
    for path in written_paths:
        print(path)


if __name__ == "__main__":
    main()
