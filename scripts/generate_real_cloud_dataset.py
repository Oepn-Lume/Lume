"""Generate a real-cloud-only training corpus in resumable batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.data_generation import run_generation_pipeline


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata", {})
    return {
        "task_id": record.get("task_id"),
        "input": record.get("input", ""),
        "target": record.get("target", ""),
        "metadata": {
            "source": "real_cloud_generation_campaign",
            "category": record.get("category"),
            "quality_score": record.get("quality_score"),
            "teacher_model": record.get("teacher_model"),
            "judge_model": record.get("judge_model"),
            "real_cloud": bool(metadata.get("real_cloud", False)),
            "difficulty": metadata.get("difficulty"),
            "template_id": metadata.get("template_id"),
            "judge_rationale": metadata.get("judge_rationale"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--min-quality", type=float, default=0.8)
    parser.add_argument("--provider", default="openai", choices=["openai"])
    parser.add_argument(
        "--campaign-root",
        default=str(ROOT / "data" / "real_cloud_campaign"),
    )
    parser.add_argument(
        "--dataset-output",
        default=str(ROOT / "data" / "datasets" / "real_cloud_generated_sft.jsonl"),
    )
    parser.add_argument("--max-batches", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    campaign_root = Path(args.campaign_root)
    dataset_output = Path(args.dataset_output)
    batches_root = campaign_root / "batches"
    batches_root.mkdir(parents=True, exist_ok=True)

    merged_records = _read_jsonl(dataset_output)
    dedupe_keys = {
        (str(record.get("input", "")).strip(), str(record.get("target", "")).strip())
        for record in merged_records
    }

    batch_index = 0
    while len(merged_records) < args.target_count:
        batch_index += 1
        if args.max_batches and batch_index > args.max_batches:
            break

        batch_root = batches_root / f"batch-{batch_index:04d}"
        manifest = run_generation_pipeline(
            output_root=batch_root,
            task_count=args.batch_size,
            min_quality=args.min_quality,
            provider=args.provider,
            require_real_cloud=True,
        )

        if not manifest.get("real_cloud", False):
            raise RuntimeError("Batch completed without real cloud. Campaign aborted.")

        batch_records = _read_jsonl(batch_root / "generated_final" / "train.jsonl")
        accepted_new = 0
        for record in batch_records:
            metadata = record.get("metadata", {})
            if not bool(metadata.get("real_cloud", False)):
                continue
            normalized = _normalize_record(record)
            dedupe_key = (
                str(normalized.get("input", "")).strip(),
                str(normalized.get("target", "")).strip(),
            )
            if dedupe_key in dedupe_keys:
                continue
            dedupe_keys.add(dedupe_key)
            merged_records.append(normalized)
            accepted_new += 1

        _write_jsonl(dataset_output, merged_records)
        _write_json(
            campaign_root / "campaign_manifest.json",
            {
                "target_count": args.target_count,
                "current_count": len(merged_records),
                "batch_size": args.batch_size,
                "min_quality": args.min_quality,
                "provider": args.provider,
                "dataset_output": str(dataset_output),
                "last_batch_index": batch_index,
                "last_batch_root": str(batch_root),
                "last_batch_new_records": accepted_new,
            },
        )

        print(
            json.dumps(
                {
                    "batch_index": batch_index,
                    "accepted_new_records": accepted_new,
                    "campaign_total": len(merged_records),
                    "target_count": args.target_count,
                    "dataset_output": str(dataset_output),
                },
                ensure_ascii=False,
            )
        )

        if accepted_new == 0:
            raise RuntimeError("Batch produced no new real-cloud records; stopping to avoid a loop.")

    print(json.dumps({"final_count": len(merged_records), "target_count": args.target_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
