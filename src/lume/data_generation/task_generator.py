"""Task generation utilities for synthetic data production."""

from __future__ import annotations

import hashlib
import random

from .schema import GeneratedTask
from .templates import TEMPLATES, TaskTemplate


def _sample_task(template: TaskTemplate, index: int, rng: random.Random) -> GeneratedTask:
    substitutions = {
        key: rng.choice(values)
        for key, values in template.substitutions.items()
    }
    prompt = template.prompt_pattern.format(**substitutions)
    suffixes = template.suffixes or []
    if suffixes:
        prompt = f"{prompt} {suffixes[index % len(suffixes)]}"
    prompt = f"{prompt} Variant #{index + 1}."
    digest = hashlib.sha1(
        f"{template.template_id}:{index}:{prompt}".encode("utf-8")
    ).hexdigest()[:10]
    return GeneratedTask(
        task_id=f"{template.template_id}-{digest}",
        category=template.category,
        template_id=template.template_id,
        prompt=prompt,
        difficulty=template.difficulty,
        metadata={"substitutions": substitutions, "variant_index": index},
    )


def generate_tasks(limit: int, *, seed: int = 42) -> list[GeneratedTask]:
    """Generate a bounded set of parameterized tasks from the template bank."""
    tasks: list[GeneratedTask] = []
    rng = random.Random(seed)
    for index in range(limit):
        template = TEMPLATES[index % len(TEMPLATES)]
        tasks.append(_sample_task(template, index, rng))
    return tasks
