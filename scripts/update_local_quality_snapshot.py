"""Build a routing-ready local quality snapshot from evaluation runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.evaluation import append_quality_history, build_quality_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v2-realcloud"),
    )
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "configs" / "local_quality.json"),
    )
    parser.add_argument(
        "--history-output",
        default=str(ROOT / "data" / "distilled" / "local_quality_history.jsonl"),
    )
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    model_root = Path(args.model_root)
    datasets_root = Path(args.datasets_root)
    payload = build_quality_snapshot(
        model_root,
        datasets_root,
        max_examples=args.max_examples,
        device=args.device,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    history_path = append_quality_history(payload, Path(args.history_output))
    print(output_path)
    print(history_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
