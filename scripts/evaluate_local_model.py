"""Evaluate the locally trained local model on current datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.evaluation import evaluate_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v1"),
    )
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "data" / "datasets" / "raw_dialogue_sft.jsonl"),
    )
    parser.add_argument("--max-examples", type=int, default=24)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = evaluate_model(
        Path(args.model_root),
        Path(args.dataset),
        max_examples=args.max_examples,
        device=args.device,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
