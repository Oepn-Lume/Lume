"""Import local Codex Desktop session logs into Lume raw logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.logging import import_codex_sessions, import_codex_sessions_incremental


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
        "--output",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import.jsonl"),
    )
    parser.add_argument(
        "--state",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import-state.json"),
    )
    parser.add_argument("--latest-only", action="store_true")
    parser.add_argument("--incremental", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.incremental:
        result = import_codex_sessions_incremental(
            Path(args.sessions_root),
            Path(args.output),
            Path(args.state),
            archived_root=Path(args.archived_root),
        )
        print(f"scanned_files={result['scanned_files']}")
        print(f"imported_records={result['imported_records']}")
    else:
        count = import_codex_sessions(
            Path(args.sessions_root),
            Path(args.output),
            latest_only=args.latest_only,
            archived_root=Path(args.archived_root),
        )
        print(f"imported_records={count}")
    print(args.output)


if __name__ == "__main__":
    main()
