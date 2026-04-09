"""Top-level synthetic data generation pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .normalize import deduplicate_samples, filter_samples, write_jsonl
from .providers import build_judge, build_teacher, provider_has_real_cloud
from .schema import GeneratedSample
from .task_generator import generate_tasks


def run_generation_pipeline(
    *,
    output_root: Path,
    task_count: int,
    min_quality: float = 0.8,
    provider: str = "mock",
    require_real_cloud: bool = False,
) -> dict[str, Any]:
    """Generate synthetic SFT data and write structured artifacts."""
    teacher = build_teacher(provider, require_real_cloud=require_real_cloud)
    judge = build_judge(provider, require_real_cloud=require_real_cloud)
    real_cloud = provider_has_real_cloud(provider) if provider != "mock" else False
    tasks = generate_tasks(task_count)

    generated_samples: list[GeneratedSample] = []
    for task in tasks:
        answer = teacher.generate(task)
        score, rationale = judge.score(task, answer)
        generated_samples.append(
            GeneratedSample(
                task_id=task.task_id,
                category=task.category,
                input=task.prompt,
                target=answer,
                quality_score=score,
                teacher_model=teacher.model_name,
                judge_model=judge.model_name,
                source_type="synthetic_cloud_factory",
                accepted=score >= min_quality,
                metadata={
                    "real_cloud": real_cloud,
                    "difficulty": task.difficulty,
                    "template_id": task.template_id,
                    "judge_rationale": rationale,
                    "substitutions": task.metadata.get("substitutions", {}),
                },
            )
        )

    deduped = deduplicate_samples(generated_samples)
    accepted = filter_samples(deduped, min_quality)

    raw_root = output_root / "generated_raw"
    scored_root = output_root / "generated_scored"
    final_root = output_root / "generated_final"
    write_jsonl(raw_root / "tasks.jsonl", [task.to_dict() for task in tasks])
    write_jsonl(scored_root / "samples_scored.jsonl", [sample.to_dict() for sample in deduped])
    write_jsonl(final_root / "train.jsonl", [sample.to_dict() for sample in accepted])

    category_counts: dict[str, int] = {}
    for sample in accepted:
        category_counts[sample.category] = category_counts.get(sample.category, 0) + 1

    manifest = {
        "requested_task_count": task_count,
        "generated_task_count": len(tasks),
        "scored_sample_count": len(deduped),
        "accepted_sample_count": len(accepted),
        "min_quality": min_quality,
        "provider": provider,
        "real_cloud": real_cloud,
        "require_real_cloud": require_real_cloud,
        "teacher_model": teacher.model_name,
        "judge_model": judge.model_name,
        "category_counts": category_counts,
        "artifacts": {
            "tasks": str(raw_root / "tasks.jsonl"),
            "scored": str(scored_root / "samples_scored.jsonl"),
            "train": str(final_root / "train.jsonl"),
        },
    }
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return manifest
