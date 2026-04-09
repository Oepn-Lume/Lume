"""Build and maintain a minimal LLM-style wiki from shadow logs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class WikiTaskEntry:
    """Structured task entry derived from a shadow log directory."""

    task_id: str
    timestamp: str
    route_mode: str
    model_used: str
    user_goal: str
    result_status: str
    value_score: float
    message_count: int
    tool_call_count: int
    file_change_count: int
    notes: str
    tool_calls: list[dict[str, Any]]
    file_changes: list[dict[str, Any]]
    messages: list[dict[str, Any]]

    @property
    def slug(self) -> str:
        return self.task_id.replace(" ", "-").lower()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = [line for line in path.read_text("utf-8").splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text("utf-8").strip()


def load_task_entry(task_dir: Path) -> WikiTaskEntry:
    """Load a task directory into a structured wiki entry."""
    task_payload = _read_json(task_dir / "task.json")
    tool_payload = _read_json(task_dir / "tool_trace.json")
    file_payload = (
        _read_json(task_dir / "file_changes.json")
        if (task_dir / "file_changes.json").exists()
        else {
            "file_changes": [
                {"path": path, "change_type": "modified", "summary": ""}
                for path in tool_payload.get("files_changed", [])
            ]
        }
    )
    messages = _read_jsonl(task_dir / "conversation.jsonl")
    if not messages and (task_dir / "prompt_response.json").exists():
        prompt_response_payload = _read_json(task_dir / "prompt_response.json")
        for pair in prompt_response_payload.get("pairs", []):
            if pair.get("prompt"):
                messages.append(
                    {"role": "user", "source": pair.get("prompt_source", "user"), "content": pair["prompt"]}
                )
            if pair.get("response"):
                messages.append(
                    {
                        "role": "assistant",
                        "source": pair.get("response_source", "assistant"),
                        "content": pair["response"],
                    }
                )
    notes = _read_optional_text(task_dir / "notes.md")
    message_count = int(task_payload.get("message_count", len(messages)))
    tool_call_count = int(task_payload.get("tool_call_count", len(tool_payload.get("tool_calls", []))))
    file_change_count = int(task_payload.get("file_change_count", len(file_payload.get("file_changes", []))))
    return WikiTaskEntry(
        task_id=task_payload["task_id"],
        timestamp=task_payload["timestamp"],
        route_mode=task_payload["route_mode"],
        model_used=task_payload["model_used"],
        user_goal=task_payload["user_goal"],
        result_status=task_payload["result_status"],
        value_score=float(task_payload["value_score"]),
        message_count=message_count,
        tool_call_count=tool_call_count,
        file_change_count=file_change_count,
        notes=notes,
        tool_calls=list(tool_payload.get("tool_calls", [])),
        file_changes=list(file_payload.get("file_changes", [])),
        messages=messages,
    )


def discover_task_entries(task_runs_root: Path) -> list[WikiTaskEntry]:
    """Discover all valid task entries under task_runs."""
    entries: list[WikiTaskEntry] = []
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.exists():
            continue
        entries.append(load_task_entry(task_dir))
    entries.sort(key=lambda entry: entry.timestamp)
    return entries


def render_task_page(entry: WikiTaskEntry) -> str:
    """Render a markdown page for a single task."""
    tool_lines = [
        f"- `{tool_call.get('tool', 'unknown')}`: {tool_call.get('output_summary', '') or 'No summary'}"
        for tool_call in entry.tool_calls
    ] or ["- None"]
    file_lines = [
        f"- `{file_change.get('path', 'unknown')}` ({file_change.get('change_type', 'modified')}): {file_change.get('summary', '') or 'No summary'}"
        for file_change in entry.file_changes
    ] or ["- None"]
    conversation_preview = [
        f"- `{message.get('source', 'unknown')}`/{message.get('role', 'unknown')}: {message.get('content', '')[:120]}"
        for message in entry.messages[:6]
    ] or ["- No conversation captured"]
    distill_signal = "high" if entry.value_score >= 0.9 else "medium" if entry.value_score >= 0.7 else "low"
    lines = [
        "---",
        f"id: {entry.slug}",
        "type: task",
        f"task_id: {entry.task_id}",
        f"updated_at: {entry.timestamp}",
        f"route_mode: {entry.route_mode}",
        f"model_used: {entry.model_used}",
        f"value_score: {entry.value_score}",
        f"distill_signal: {distill_signal}",
        "---",
        "",
        f"# {entry.task_id}",
        "",
        "## User Goal",
        entry.user_goal,
        "",
        "## Summary",
        f"- Timestamp: {entry.timestamp}",
        f"- Result Status: {entry.result_status}",
        f"- Messages: {entry.message_count}",
        f"- Tool Calls: {entry.tool_call_count}",
        f"- File Changes: {entry.file_change_count}",
        "",
        "## Conversation Preview",
        *conversation_preview,
        "",
        "## Tool Actions",
        *tool_lines,
        "",
        "## File Results",
        *file_lines,
        "",
        "## Reuse Notes",
        entry.notes or "No notes recorded.",
        "",
        "## Distill Readiness",
        f"This task currently has a `{distill_signal}` distillation signal based on value score {entry.value_score}.",
        "",
    ]
    return "\n".join(lines)


def render_index(entries: list[WikiTaskEntry]) -> str:
    """Render the wiki index page."""
    lines = [
        "# Lume Wiki Index",
        "",
        "## Task Pages",
    ]
    if not entries:
        lines.append("- No task pages yet.")
    else:
        for entry in entries:
            lines.append(
                f"- [{entry.task_id}](tasks/{entry.slug}.md) | {entry.timestamp} | score={entry.value_score}"
            )
    lines.extend(
        [
            "",
            "## Notes",
            "- This index is generated from `data/task_runs/` shadow logs.",
            "- Higher value scores indicate stronger candidates for distillation.",
            "",
        ]
    )
    return "\n".join(lines)


def render_log(entries: list[WikiTaskEntry]) -> str:
    """Render the wiki update log."""
    lines = [
        "# Lume Wiki Log",
        "",
    ]
    if not entries:
        lines.append("- No updates yet.")
    else:
        for entry in entries:
            lines.append(
                f"- {entry.timestamp} | `{entry.task_id}` | route={entry.route_mode} | score={entry.value_score}"
            )
    lines.append("")
    return "\n".join(lines)


def build_wiki(task_runs_root: Path, wiki_root: Path) -> list[Path]:
    """Generate wiki pages, index, and log from shadow logs."""
    wiki_root.mkdir(parents=True, exist_ok=True)
    tasks_root = wiki_root / "tasks"
    tasks_root.mkdir(parents=True, exist_ok=True)

    entries = discover_task_entries(task_runs_root)
    written_paths: list[Path] = []

    for entry in entries:
        task_page_path = tasks_root / f"{entry.slug}.md"
        task_page_path.write_text(render_task_page(entry) + "\n", "utf-8")
        written_paths.append(task_page_path)

    index_path = wiki_root / "index.md"
    index_path.write_text(render_index(entries) + "\n", "utf-8")
    written_paths.append(index_path)

    log_path = wiki_root / "log.md"
    log_path.write_text(render_log(entries) + "\n", "utf-8")
    written_paths.append(log_path)

    return written_paths
