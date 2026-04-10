"""Build and maintain a minimal LLM-style wiki from tasks, docs, and analyses."""

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


@dataclass(slots=True)
class WikiDocEntry:
    """Structured document entry derived from docs/ files."""

    slug: str
    relative_path: str
    title: str
    language: str
    section: str
    body: str


@dataclass(slots=True)
class WikiAnalysisEntry:
    """Structured analytical entry derived from comparison reports."""

    slug: str
    title: str
    section: str
    summary: str
    details: list[str]


@dataclass(slots=True)
class WikiStaticEntry:
    """A manually maintained wiki entry kept directly under the repository wiki/ tree."""

    slug: str
    title: str
    section: str
    relative_path: str


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


def _slugify(value: str) -> str:
    return (
        value.replace("\\", "-")
        .replace("/", "-")
        .replace(" ", "-")
        .replace(".", "-")
        .replace(":", "-")
        .lower()
    )


def _infer_title(relative_path: str, body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return Path(relative_path).stem.replace("-", " ").replace("_", " ").title()


def _infer_language(relative_path: str) -> str:
    lowered = relative_path.lower()
    if "/en/" in lowered or lowered.startswith("en/"):
        return "en"
    if lowered.endswith(".zh-cn.md") or "zhihu" in lowered or "中文" in lowered:
        return "zh"
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in lowered) else "mixed"


def _section_from_relative_path(relative_path: str) -> str:
    parts = relative_path.split("/")
    if len(parts) > 1:
        return parts[0]
    return "root"


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


def discover_doc_entries(docs_root: Path) -> list[WikiDocEntry]:
    """Discover all docs/ files and convert them into wiki entries."""
    entries: list[WikiDocEntry] = []
    for path in sorted(docs_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        body = path.read_text("utf-8", errors="ignore").strip()
        if not body:
            continue
        relative_path = path.relative_to(docs_root).as_posix()
        entries.append(
            WikiDocEntry(
                slug=_slugify(relative_path),
                relative_path=relative_path,
                title=_infer_title(relative_path, body),
                language=_infer_language(relative_path),
                section=_section_from_relative_path(relative_path),
                body=body,
            )
        )
    return entries


def discover_analysis_entries(reports_root: Path) -> list[WikiAnalysisEntry]:
    """Discover analytical entries from the full Gemma vs Cloud comparison report."""
    report_path = reports_root / "gemma_vs_cloud_all_sessions.json"
    if not report_path.exists():
        return []
    payload = _read_json(report_path)
    summary = payload.get("summary", {})
    analyses: list[WikiAnalysisEntry] = []

    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-overview",
            title="Gemma vs Cloud Overview",
            section="gemma-vs-cloud",
            summary="Top-level coverage, replay volume, and headline quality metrics from the full retained session history.",
            details=[
                f"Session files scanned: {summary.get('session_file_count', 0)}",
                f"Comparable replies replayed: {summary.get('comparison_count', 0)}",
                f"Supplemental codex/cloud events exported: {summary.get('supplemental_event_count', 0)}",
                f"Average similarity: {summary.get('avg_similarity', 0.0)}",
                f"Cloud average reply length: {summary.get('cloud_avg_char_len', 0.0)}",
                f"Gemma average reply length: {summary.get('gemma_avg_char_len', 0.0)}",
            ],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-context-gap",
            title="Gemma Context Continuation Gap",
            section="gemma-vs-cloud",
            summary="Gemma often answers as a general-purpose advisor, while the cloud continues the live thread state and acts as an in-progress collaborator.",
            details=[
                "Gemma tends to elaborate and generalize instead of continuing from the active task state.",
                "Short context-heavy prompts such as 'continue', 'publish', or 'too long' are often handled correctly by the cloud but reset by Gemma into generic clarification behavior.",
                "This gap explains why the average similarity remains low even when Gemma produces plausible standalone text.",
            ],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-developer-chain",
            title="Developer and Codex Internal Message Gap",
            section="gemma-vs-cloud",
            summary="The replay set includes developer/codex-to-cloud turns, exposing a second gap: Gemma does not yet read internal workflow signals the way the cloud model does.",
            details=[
                f"Prompt role counts: {summary.get('prompt_role_counts', {})}",
                "Internal command approvals, repo-state updates, and execution control messages are often treated by Gemma as plain text rather than workflow state.",
                "This is a key training direction for turning a local model into a collaborative runtime agent instead of a standalone chat assistant.",
            ],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-code-overproduction",
            title="Gemma Overproduces Code",
            section="gemma-vs-cloud",
            summary="Gemma emits code and solution templates more often than the cloud, even when the live task primarily needs state continuation or concise execution guidance.",
            details=[
                f"Cloud code rate: {summary.get('cloud_code_rate', 0.0)}",
                f"Gemma code rate: {summary.get('gemma_code_rate', 0.0)}",
                "This does not mean Gemma is better at coding; it means Gemma switches into generic solution mode too early.",
                "The cloud keeps more replies in execution-followup mode instead of template-generation mode.",
            ],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-process-events",
            title="Process Event Coverage",
            section="gemma-vs-cloud",
            summary="The comparison preserved non-chat process events so the wiki retains the codex/cloud working chain, not just final replies.",
            details=[
                f"Top supplemental events: {summary.get('supplemental_event_counts', {})}",
                "Function calls, function-call outputs, reasoning traces, command completion events, and patch events are all retained.",
                "These events are essential if the local model is meant to learn how cloud collaboration actually progresses through work.",
            ],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-lowest-similarity",
            title="Lowest Similarity Cases",
            section="gemma-vs-cloud",
            summary="These entries capture the most instructive failures where Gemma diverged sharply from the cloud continuation behavior.",
            details=[
                json.dumps(example, ensure_ascii=False)
                for example in summary.get("lowest_similarity_examples", [])
            ]
            or ["No examples recorded."],
        )
    )
    analyses.append(
        WikiAnalysisEntry(
            slug="gemma-vs-cloud-code-mismatch",
            title="Code Mismatch Cases",
            section="gemma-vs-cloud",
            summary="These examples show where the cloud stayed grounded in the active repo/task context while Gemma drifted into generic advisory or template output.",
            details=[
                json.dumps(example, ensure_ascii=False)
                for example in summary.get("code_mismatch_examples", [])
            ]
            or ["No examples recorded."],
        )
    )
    return analyses


def discover_static_entries(wiki_root: Path, section: str) -> list[WikiStaticEntry]:
    """Discover manually maintained wiki pages under sections like milestones/ or memory/."""
    section_root = wiki_root / section
    if not section_root.exists():
        return []
    entries: list[WikiStaticEntry] = []
    for path in sorted(section_root.rglob("*.md")):
        if not path.is_file():
            continue
        body = path.read_text("utf-8", errors="ignore").strip()
        title = _infer_title(path.relative_to(wiki_root).as_posix(), body)
        entries.append(
            WikiStaticEntry(
                slug=_slugify(path.relative_to(wiki_root).as_posix()),
                title=title,
                section=section,
                relative_path=path.relative_to(wiki_root).as_posix(),
            )
        )
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


def render_doc_page(entry: WikiDocEntry, docs_root: Path) -> str:
    """Render a markdown page for a docs entry, preserving the full source body."""
    lines = [
        "---",
        f"id: {entry.slug}",
        "type: doc",
        f"relative_path: {entry.relative_path}",
        f"language: {entry.language}",
        f"section: {entry.section}",
        "---",
        "",
        f"# {entry.title}",
        "",
        "## Source",
        f"- Path: `{entry.relative_path}`",
        f"- Language: `{entry.language}`",
        f"- Section: `{entry.section}`",
        f"- Original file: [{entry.relative_path}]({(docs_root / entry.relative_path).resolve().as_posix()})",
        "",
        "## Body",
        "",
        entry.body,
        "",
    ]
    return "\n".join(lines)


def render_analysis_page(entry: WikiAnalysisEntry) -> str:
    """Render a markdown page for an analytical entry."""
    lines = [
        "---",
        f"id: {entry.slug}",
        "type: analysis",
        f"section: {entry.section}",
        "---",
        "",
        f"# {entry.title}",
        "",
        "## Summary",
        entry.summary,
        "",
        "## Details",
        *[f"- {detail}" for detail in entry.details],
        "",
    ]
    return "\n".join(lines)


def render_index(
    task_entries: list[WikiTaskEntry],
    doc_entries: list[WikiDocEntry],
    analysis_entries: list[WikiAnalysisEntry],
    milestone_entries: list[WikiStaticEntry] | None = None,
    memory_entries: list[WikiStaticEntry] | None = None,
) -> str:
    """Render the wiki index page."""
    milestone_entries = milestone_entries or []
    memory_entries = memory_entries or []
    lines = [
        "# Lume Wiki Index",
        "",
        "## Task Pages",
    ]
    if not task_entries:
        lines.append("- No task pages yet.")
    else:
        for entry in task_entries:
            lines.append(
                f"- [{entry.task_id}](tasks/{entry.slug}.md) | {entry.timestamp} | score={entry.value_score}"
            )

    lines.extend(["", "## Document Pages"])
    if not doc_entries:
        lines.append("- No document pages yet.")
    else:
        for entry in doc_entries:
            lines.append(
                f"- [{entry.title}](docs/{entry.slug}.md) | path=`{entry.relative_path}` | lang={entry.language}"
            )

    lines.extend(["", "## Analysis Pages"])
    if not analysis_entries:
        lines.append("- No analysis pages yet.")
    else:
        for entry in analysis_entries:
            lines.append(f"- [{entry.title}](analysis/{entry.slug}.md) | section={entry.section}")

    lines.extend(["", "## Milestones"])
    if not milestone_entries:
        lines.append("- No milestone pages yet.")
    else:
        for entry in milestone_entries:
            lines.append(f"- [{entry.title}]({entry.relative_path})")

    lines.extend(["", "## Memory"])
    if not memory_entries:
        lines.append("- No memory pages yet.")
    else:
        for entry in memory_entries:
            lines.append(f"- [{entry.title}]({entry.relative_path})")

    lines.extend(
        [
            "",
            "## Notes",
            "- Task pages are generated from `data/task_runs/` shadow logs.",
            "- Document pages mirror the current `docs/` knowledge base.",
            "- Analysis pages capture durable findings from large comparisons such as the Gemma vs Cloud replay.",
            "- Milestone pages record major implementation steps that should remain visible in repo history.",
            "- Memory pages store durable operating rules for how future milestone actions should be logged.",
            "",
        ]
    )
    return "\n".join(lines)


def render_log(
    task_entries: list[WikiTaskEntry],
    doc_entries: list[WikiDocEntry],
    analysis_entries: list[WikiAnalysisEntry],
    milestone_entries: list[WikiStaticEntry] | None = None,
    memory_entries: list[WikiStaticEntry] | None = None,
) -> str:
    """Render the wiki update log."""
    milestone_entries = milestone_entries or []
    memory_entries = memory_entries or []
    lines = ["# Lume Wiki Log", ""]
    if not task_entries and not doc_entries and not analysis_entries and not milestone_entries and not memory_entries:
        lines.append("- No updates yet.")
        lines.append("")
        return "\n".join(lines)

    for entry in task_entries:
        lines.append(f"- {entry.timestamp} | task `{entry.task_id}` | route={entry.route_mode} | score={entry.value_score}")
    for entry in doc_entries:
        lines.append(f"- docs | `{entry.relative_path}` | title={entry.title} | lang={entry.language}")
    for entry in analysis_entries:
        lines.append(f"- analysis | `{entry.slug}` | title={entry.title}")
    for entry in milestone_entries:
        lines.append(f"- milestones | `{entry.relative_path}` | title={entry.title}")
    for entry in memory_entries:
        lines.append(f"- memory | `{entry.relative_path}` | title={entry.title}")
    lines.append("")
    return "\n".join(lines)


def build_wiki(task_runs_root: Path, wiki_root: Path, docs_root: Path | None = None, reports_root: Path | None = None) -> list[Path]:
    """Generate wiki pages, index, and log from tasks, docs, and analyses."""
    wiki_root.mkdir(parents=True, exist_ok=True)
    tasks_root = wiki_root / "tasks"
    docs_pages_root = wiki_root / "docs"
    analysis_root = wiki_root / "analysis"
    milestone_root = wiki_root / "milestones"
    memory_root = wiki_root / "memory"
    tasks_root.mkdir(parents=True, exist_ok=True)
    docs_pages_root.mkdir(parents=True, exist_ok=True)
    analysis_root.mkdir(parents=True, exist_ok=True)
    milestone_root.mkdir(parents=True, exist_ok=True)
    memory_root.mkdir(parents=True, exist_ok=True)

    task_entries = discover_task_entries(task_runs_root)
    doc_entries = discover_doc_entries(docs_root) if docs_root is not None and docs_root.exists() else []
    analysis_entries = discover_analysis_entries(reports_root) if reports_root is not None and reports_root.exists() else []
    milestone_entries = discover_static_entries(wiki_root, "milestones")
    memory_entries = discover_static_entries(wiki_root, "memory")
    written_paths: list[Path] = []

    for entry in task_entries:
        task_page_path = tasks_root / f"{entry.slug}.md"
        task_page_path.write_text(render_task_page(entry) + "\n", "utf-8")
        written_paths.append(task_page_path)

    for entry in doc_entries:
        doc_page_path = docs_pages_root / f"{entry.slug}.md"
        doc_page_path.write_text(render_doc_page(entry, docs_root) + "\n", "utf-8")
        written_paths.append(doc_page_path)

    for entry in analysis_entries:
        analysis_page_path = analysis_root / f"{entry.slug}.md"
        analysis_page_path.write_text(render_analysis_page(entry) + "\n", "utf-8")
        written_paths.append(analysis_page_path)

    index_path = wiki_root / "index.md"
    index_path.write_text(
        render_index(
            task_entries,
            doc_entries,
            analysis_entries,
            milestone_entries=milestone_entries,
            memory_entries=memory_entries,
        )
        + "\n",
        "utf-8",
    )
    written_paths.append(index_path)

    log_path = wiki_root / "log.md"
    log_path.write_text(
        render_log(
            task_entries,
            doc_entries,
            analysis_entries,
            milestone_entries=milestone_entries,
            memory_entries=memory_entries,
        )
        + "\n",
        "utf-8",
    )
    written_paths.append(log_path)

    return written_paths
