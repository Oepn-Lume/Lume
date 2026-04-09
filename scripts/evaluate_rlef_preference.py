"""Evaluate a preference-optimized adapter on the RLEF preference dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.rl import evaluate_preference_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        default=str(ROOT / "data" / "distilled" / "transformers-dpo-v1"),
    )
    parser.add_argument(
        "--dataset-path",
        default=str(ROOT / "data" / "datasets" / "rlef_preference.jsonl"),
    )
    parser.add_argument("--max-examples", type=int, default=32)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--output-path",
        default=str(ROOT / "data" / "distilled" / "rlef" / "preference_eval.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = evaluate_preference_model(
        Path(args.model_root),
        Path(args.dataset_path),
        max_examples=args.max_examples,
        device=args.device,
    )
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
