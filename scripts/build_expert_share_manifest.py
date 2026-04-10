"""Build a local expert share manifest for future Digital Sun synchronization."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.swarm import build_weight_share_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expert-name", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--source-node", default="local-node")
    parser.add_argument("--quality-score", type=float, default=0.5)
    parser.add_argument("--reward-score", type=float, default=0.5)
    parser.add_argument("--adapter-path", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--output-path",
        default=str(ROOT / "data" / "distilled" / "swarm" / "expert_share_manifest.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_weight_share_manifest(
        output_path=Path(args.output_path),
        expert_name=args.expert_name,
        domain=args.domain,
        source_node=args.source_node,
        quality_score=args.quality_score,
        reward_score=args.reward_score,
        adapter_path=args.adapter_path or None,
        notes=args.notes,
    )
    print(path)


if __name__ == "__main__":
    main()
