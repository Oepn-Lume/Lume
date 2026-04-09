"""Train a minimal preference-optimized LoRA adapter from RLEF data."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.rl import PreferenceTrainingConfig, train_preference_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path",
        default=str(ROOT / "data" / "datasets" / "rlef_preference.jsonl"),
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "transformers-dpo-v1"),
    )
    parser.add_argument("--model-name-or-path", default="uer/gpt2-chinese-cluecorpussmall")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = PreferenceTrainingConfig(
        dataset_path=args.dataset_path,
        output_root=args.output_root,
        model_name_or_path=args.model_name_or_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        max_length=args.max_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        beta=args.beta,
        max_samples=args.max_samples,
        device=args.device,
    )
    print(train_preference_model(config))


if __name__ == "__main__":
    main()
