"""Generate a response from the locally trained local model."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.evaluation import generate_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--model-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v1"),
    )
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt = f"User:\n{args.prompt}\n\nAssistant:\n"
    print(
        generate_text(
            Path(args.model_root),
            prompt,
            max_new_tokens=args.max_new_tokens,
            device=args.device,
        )
    )


if __name__ == "__main__":
    main()
