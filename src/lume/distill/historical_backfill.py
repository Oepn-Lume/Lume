"""Backfill historical workspace artifacts into trainable datasets."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path


INCLUDE_DIRS = {"src", "scripts", "tests", "configs"}
INCLUDE_FILES = {"README.md"}
INCLUDE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".sh",
    ".ps1",
}


def _iter_candidate_files(lume_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for child in lume_root.iterdir():
        if child.is_dir() and child.name in INCLUDE_DIRS:
            for path in child.rglob("*"):
                if not path.is_file():
                    continue
                if "__pycache__" in path.parts:
                    continue
                if path.suffix.lower() not in INCLUDE_EXTENSIONS:
                    continue
                candidates.append(path)
        elif child.is_file() and child.name in INCLUDE_FILES:
            candidates.append(child)
    return sorted(candidates)


def _describe_path(lume_root: Path, path: Path) -> str:
    relative_path = path.relative_to(lume_root).as_posix()
    top_level = relative_path.split("/", 1)[0]
    if top_level == "src":
        return "Historical source module from the Lume codebase."
    if top_level == "scripts":
        return "Historical executable script from the Lume workflow."
    if top_level == "tests":
        return "Historical test artifact covering a Lume behavior."
    if top_level == "configs":
        return "Historical configuration artifact used by the Lume system."
    return "Historical workspace artifact from the Lume project."


def build_historical_workspace_dataset(lume_root: Path, datasets_root: Path) -> Path:
    """Backfill current workspace files into a historical code dataset."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "historical_workspace_code_sft.jsonl"
    records: list[dict[str, object]] = []
    for index, path in enumerate(_iter_candidate_files(lume_root)):
        try:
            content = path.read_text("utf-8")
        except UnicodeDecodeError:
            continue
        if not content.strip():
            continue
        relative_path = path.relative_to(lume_root).as_posix()
        timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
        records.append(
            {
                "task_id": f"historical-workspace-{index}",
                "input": (
                    f"{_describe_path(lume_root, path)}\n"
                    f"Path: {relative_path}\n"
                    "Objective: Preserve this existing workspace artifact as a reusable training sample."
                ),
                "target": content,
                "metadata": {
                    "source": "historical_workspace_backfill",
                    "relative_path": relative_path,
                    "suffix": path.suffix.lower(),
                    "modified_at": timestamp,
                },
            }
        )

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )
    return output_path
