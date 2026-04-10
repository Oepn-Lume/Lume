"""Build expert-specific datasets and train a first-pass adapter per battery expert."""

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

from lume.battery import load_expert_profiles
from lume.distill import (
    DEFAULT_STAGE_ONE_DATASET_FILES,
    TrainingConfig,
    build_battery_state_dataset,
    normalize_dataset_files,
    train_local_model,
)

STAGE_TWO_CANDIDATE_FILES = [
    "battery_state_sft.jsonl",
    "battery_cascade_sft.jsonl",
    "hybrid_refinement_sft.jsonl",
    "codex_action_sft.jsonl",
    "continue_state_sft.jsonl",
    "developer_chain_sft.jsonl",
    "historical_workspace_code_sft.jsonl",
    "memory_update.jsonl",
    "onsite_alignment_sft.jsonl",
]

DOMAIN_CORE_FILES = {
    "general": ["battery_state_sft.jsonl", "codex_action_sft.jsonl", "memory_update.jsonl"],
    "code": [
        "battery_state_sft.jsonl",
        "battery_cascade_sft.jsonl",
        "codex_action_sft.jsonl",
        "continue_state_sft.jsonl",
        "historical_workspace_code_sft.jsonl",
        "hybrid_refinement_sft.jsonl",
    ],
    "creative": ["raw_dialogue_sft.jsonl", "real_cloud_dialogue_sft.jsonl", "synthetic_sft.jsonl", "memory_update.jsonl"],
    "reasoning": ["battery_state_sft.jsonl", "developer_chain_sft.jsonl", "onsite_alignment_sft.jsonl", "sft_reasoning.jsonl"],
    "private": ["battery_state_sft.jsonl", "memory_update.jsonl", "raw_dialogue_sft.jsonl"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--battery-matrix-config", default=str(ROOT / "configs" / "battery_matrix.yaml"))
    parser.add_argument("--task-runs-root", default=str(ROOT / "data" / "task_runs"))
    parser.add_argument("--source-datasets-root", default=str(ROOT / "data" / "datasets"))
    parser.add_argument("--expert-datasets-root", default=str(ROOT / "data" / "datasets_experts"))
    parser.add_argument("--models-root", default=str(ROOT / "data" / "distilled" / "experts"))
    parser.add_argument("--shared-foundation-root", default=str(ROOT / "data" / "distilled" / "experts" / "shared-foundation"))
    parser.add_argument("--model-name-or-path", default="uer/gpt2-chinese-cluecorpussmall")
    parser.add_argument("--training-mode", default="transformers_peft_lora")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--skip-training", action="store_true")
    parser.add_argument("--report-output", default=str(ROOT / "data" / "reports" / "expert_adapter_pipeline_report.json"))
    return parser.parse_args()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )


def _combined_text(record: dict[str, Any]) -> str:
    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    parts = [
        str(record.get("input", "")),
        json.dumps(record.get("target", ""), ensure_ascii=False),
        json.dumps(metadata, ensure_ascii=False),
    ]
    return "\n".join(parts).lower()


def _score_record(record: dict[str, Any], *, domain: str, keywords: list[str], filename: str) -> int:
    text = _combined_text(record)
    score = 0
    if filename in DOMAIN_CORE_FILES.get(domain, []):
        score += 2
    if domain and domain in text:
        score += 2
    for keyword in keywords:
        if keyword and keyword.lower() in text:
            score += 2
    metadata = record.get("metadata", {})
    if isinstance(metadata, dict):
        if str(metadata.get("expert_domain", "")).lower() == domain:
            score += 3
        if str(metadata.get("primary_expert", "")).lower() and domain == "general":
            score += 1
    return score


def _filter_records(
    records: list[dict[str, Any]],
    *,
    domain: str,
    keywords: list[str],
    filename: str,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        score = _score_record(record, domain=domain, keywords=keywords, filename=filename)
        if score > 0:
            clone = dict(record)
            metadata = clone.get("metadata", {})
            metadata = dict(metadata) if isinstance(metadata, dict) else {}
            metadata["expert_split_domain"] = domain
            metadata["expert_split_source_file"] = filename
            metadata["expert_split_score"] = score
            clone["metadata"] = metadata
            scored.append((score, clone))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [record for _score, record in scored]


def _train_expert_adapter(
    *,
    expert_name: str,
    datasets_root: Path,
    output_root: Path,
    shared_foundation_root: Path,
    args: argparse.Namespace,
) -> Path:
    available_files = [path.name for path in sorted(datasets_root.glob("*.jsonl"))]
    config = TrainingConfig(
        datasets_root=str(datasets_root),
        output_root=str(output_root),
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_samples=args.max_samples,
        device=args.device,
        training_mode=args.training_mode,
        model_name_or_path=args.model_name_or_path,
        max_length=args.max_length,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        dataset_files=normalize_dataset_files(available_files),
        init_adapter_path=str(shared_foundation_root / "adapter"),
        stage_name=f"expert_{expert_name}",
    )
    return train_local_model(config)


def main() -> None:
    args = parse_args()
    source_datasets_root = Path(args.source_datasets_root)
    task_runs_root = Path(args.task_runs_root)
    expert_datasets_root = Path(args.expert_datasets_root)
    models_root = Path(args.models_root)
    shared_foundation_root = Path(args.shared_foundation_root)
    report_output = Path(args.report_output)

    build_battery_state_dataset(task_runs_root, source_datasets_root)
    experts = load_expert_profiles(Path(args.battery_matrix_config))

    report: dict[str, Any] = {
        "battery_matrix_config": args.battery_matrix_config,
        "source_datasets_root": str(source_datasets_root),
        "expert_datasets_root": str(expert_datasets_root),
        "shared_foundation_root": str(shared_foundation_root),
        "models_root": str(models_root),
        "skip_training": args.skip_training,
        "foundation_dataset_files": DEFAULT_STAGE_ONE_DATASET_FILES,
        "experts": {},
    }

    if not args.skip_training:
        foundation_config = TrainingConfig(
            datasets_root=str(source_datasets_root),
            output_root=str(shared_foundation_root),
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_samples=args.max_samples,
            device=args.device,
            training_mode=args.training_mode,
            model_name_or_path=args.model_name_or_path,
            max_length=args.max_length,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            dataset_files=normalize_dataset_files(DEFAULT_STAGE_ONE_DATASET_FILES),
            stage_name="expert_shared_foundation",
        )
        foundation_root = train_local_model(foundation_config)
        report["shared_foundation_trained_root"] = str(foundation_root)

    for expert in experts:
        dataset_root = expert_datasets_root / expert.name
        dataset_root.mkdir(parents=True, exist_ok=True)
        expert_report: dict[str, Any] = {
            "domain": expert.domain,
            "keywords": expert.keywords,
            "dataset_files": {},
        }
        candidate_files = sorted(set(STAGE_TWO_CANDIDATE_FILES + DOMAIN_CORE_FILES.get(expert.domain, [])))
        for filename in candidate_files:
            source_path = source_datasets_root / filename
            if not source_path.exists():
                continue
            records = _read_jsonl(source_path)
            filtered = _filter_records(
                records,
                domain=expert.domain,
                keywords=expert.keywords,
                filename=filename,
            )
            if not filtered:
                continue
            _write_jsonl(dataset_root / filename, filtered)
            expert_report["dataset_files"][filename] = len(filtered)

        if not args.skip_training and expert_report["dataset_files"]:
            model_root = _train_expert_adapter(
                expert_name=expert.name,
                datasets_root=dataset_root,
                output_root=models_root / expert.name,
                shared_foundation_root=shared_foundation_root,
                args=args,
            )
            expert_report["model_root"] = str(model_root)
            expert_report["adapter_path"] = str(Path(model_root) / "adapter")

        report["experts"][expert.name] = expert_report

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
