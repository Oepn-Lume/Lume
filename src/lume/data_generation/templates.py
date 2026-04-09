"""Template bank for synthetic high-value task generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskTemplate:
    template_id: str
    category: str
    difficulty: str
    prompt_pattern: str
    substitutions: dict[str, list[str]]
    suffixes: list[str] | None = None


TEMPLATES: list[TaskTemplate] = [
    TaskTemplate(
        template_id="doc-readme",
        category="documentation",
        difficulty="medium",
        prompt_pattern="Write a concise README section for a {system} feature focused on {goal}.",
        substitutions={
            "system": ["memory pipeline", "shadow logging", "training sync", "wiki memory"],
            "goal": ["setup", "debugging", "daily usage", "architecture overview"],
        },
        suffixes=[
            "Keep it practical.",
            "Include a troubleshooting note.",
            "Emphasize reuse.",
            "Add one short warning about misuse.",
        ],
    ),
    TaskTemplate(
        template_id="code-refactor",
        category="coding",
        difficulty="high",
        prompt_pattern="Refactor a {language} module that currently handles {problem} and explain the safer design.",
        substitutions={
            "language": ["Python", "TypeScript", "Rust"],
            "problem": ["logging state", "tool routing", "dataset deduplication", "memory updates"],
        },
        suffixes=[
            "Explain the tradeoff in one paragraph.",
            "Mention one likely regression risk.",
            "Favor maintainability over cleverness.",
            "Include a verification checklist.",
        ],
    ),
    TaskTemplate(
        template_id="review-risk",
        category="review",
        difficulty="medium",
        prompt_pattern="Review a change that modifies {component} and list the most likely regression risks.",
        substitutions={
            "component": ["API routing", "session import", "wiki generation", "GPU training pipeline"],
        },
        suffixes=[
            "Order findings by severity.",
            "Focus on behavioral regressions.",
            "Assume the code is already deployed.",
            "Mention missing tests explicitly.",
        ],
    ),
    TaskTemplate(
        template_id="memory-extract",
        category="memory",
        difficulty="low",
        prompt_pattern="From a task log about {topic}, extract reusable workflow knowledge and user preference notes.",
        substitutions={
            "topic": ["architectural planning", "bug fixing", "training setup", "document writing"],
        },
        suffixes=[
            "Separate workflow from preference.",
            "Highlight what should be remembered long-term.",
            "Keep the memory entry compact.",
            "Mark what is reusable vs. situational.",
        ],
    ),
    TaskTemplate(
        template_id="creative-brief",
        category="creative",
        difficulty="medium",
        prompt_pattern="Write a {style} piece about {theme} with a strong ending and clear imagery.",
        substitutions={
            "style": ["short essay", "speech", "prose poem", "manifesto"],
            "theme": ["nation and ordinary people", "technology and memory", "builders and tools", "future local AI"],
        },
        suffixes=[
            "End on a hopeful image.",
            "Keep the tone vivid but controlled.",
            "Avoid empty slogans.",
            "Make the final paragraph memorable.",
        ],
    ),
]
