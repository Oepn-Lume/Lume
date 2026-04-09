"""Generate a large synthetic training corpus using the Lume data factory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.data_generation import run_generation_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-count", type=int, default=1000)
    parser.add_argument("--min-quality", type=float, default=0.8)
    parser.add_argument("--provider", default="mock", choices=["mock", "openai"])
    parser.add_argument("--require-real-cloud", action="store_true")
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "generated_corpus"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_generation_pipeline(
        output_root=Path(args.output_root),
        task_count=args.task_count,
        min_quality=args.min_quality,
        provider=args.provider,
        require_real_cloud=args.require_real_cloud,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
