"""Incrementally sync Codex sessions into training data and optionally retrain."""

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
from lume.distill import (
    build_distill_datasets,
    merge_synthetic_corpus,
    TrainingConfig,
    train_local_model,
)
from lume.evaluation import build_quality_snapshot
from lume.logging import import_codex_sessions_incremental


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
        "--raw-output",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import.jsonl"),
    )
    parser.add_argument(
        "--state",
        default=str(ROOT / "data" / "raw_logs" / "codex-session-import-state.json"),
    )
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--raw-logs-root",
        default=str(ROOT / "data" / "raw_logs"),
    )
    parser.add_argument(
        "--distilled-root",
        default=str(ROOT / "data" / "distilled" / "transformers-lora-v1"),
    )
    parser.add_argument("--synthetic-task-count", type=int, default=0)
    parser.add_argument("--synthetic-provider", default="mock", choices=["mock", "openai"])
    parser.add_argument(
        "--generated-root",
        default=str(ROOT / "data" / "generated_corpus"),
    )
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--block-size", type=int, default=192)
    parser.add_argument("--embed-dim", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=128)
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
    parser.add_argument("--skip-quality-update", action="store_true")
    parser.add_argument("--quality-max-examples", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import_result = import_codex_sessions_incremental(
        Path(args.sessions_root),
        Path(args.raw_output),
        Path(args.state),
        archived_root=Path(args.archived_root),
    )
    print(f"scanned_files={import_result['scanned_files']}")
    print(f"imported_records={import_result['imported_records']}")

    if args.synthetic_task_count > 0:
        manifest = run_generation_pipeline(
            output_root=Path(args.generated_root),
            task_count=args.synthetic_task_count,
            min_quality=0.8,
            provider=args.synthetic_provider,
        )
        print(f"synthetic_generated={manifest['generated_task_count']}")
        print(f"synthetic_accepted={manifest['accepted_sample_count']}")
        synthetic_path = merge_synthetic_corpus(
            Path(args.generated_root),
            Path(args.datasets_root),
        )
        print(synthetic_path)

    dataset_paths = build_distill_datasets(
        Path(args.task_runs_root),
        Path(args.datasets_root),
        Path(args.raw_logs_root),
    )
    for path in dataset_paths:
        print(path)

    if args.skip_train:
        return

    output_root = train_local_model(
        TrainingConfig(
            datasets_root=args.datasets_root,
            output_root=args.distilled_root,
            epochs=args.epochs,
            batch_size=args.batch_size,
            block_size=args.block_size,
            embed_dim=args.embed_dim,
            hidden_dim=args.hidden_dim,
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
    )
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
    print(quality_path)


if __name__ == "__main__":
    main()
