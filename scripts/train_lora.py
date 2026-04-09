"""Train the current Lume datasets with transformers + PEFT/LoRA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import TrainingConfig, train_local_model
from lume.evaluation import append_quality_history, build_quality_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v1"),
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--embed-dim", type=int, default=96)
    parser.add_argument("--hidden-dim", type=int, default=192)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--training-mode", default="auto")
    parser.add_argument("--model-name-or-path", default="uer/gpt2-chinese-cluecorpussmall")
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument(
        "--quality-output",
        default=str(ROOT / "configs" / "local_quality.json"),
    )
    parser.add_argument(
        "--quality-history-output",
        default=str(ROOT / "data" / "distilled" / "local_quality_history.jsonl"),
    )
    parser.add_argument("--skip-quality-update", action="store_true")
    parser.add_argument("--quality-max-examples", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = TrainingConfig(
        datasets_root=args.datasets_root,
        output_root=args.output_root,
        epochs=args.epochs,
        batch_size=args.batch_size,
        block_size=args.block_size,
        embed_dim=args.embed_dim,
        hidden_dim=args.hidden_dim,
        learning_rate=args.learning_rate,
        max_samples=args.max_samples,
        device=args.device,
        training_mode=args.training_mode,
        model_name_or_path=args.model_name_or_path,
        max_length=args.max_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
    )
    output_root = train_local_model(config)
    print(output_root)
    if args.skip_quality_update:
        return
    snapshot = build_quality_snapshot(
        Path(output_root),
        Path(args.datasets_root),
        max_examples=args.quality_max_examples,
        device=args.device,
    )
    quality_path = Path(args.quality_output)
    quality_path.parent.mkdir(parents=True, exist_ok=True)
    quality_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", "utf-8")
    history_path = append_quality_history(snapshot, Path(args.quality_history_output))
    print(quality_path)
    print(history_path)


if __name__ == "__main__":
    main()
