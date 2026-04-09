from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.memory import build_wiki


def test_build_wiki_generates_index_log_and_task_page(tmp_path: Path) -> None:
    task_runs_root = tmp_path / "task_runs"
    task_dir = task_runs_root / "task-1"
    task_dir.mkdir(parents=True)

    (task_dir / "task.json").write_text(
        """{
  "task_id": "task-1",
  "session_id": "task-1",
  "timestamp": "2026-04-09T00:00:00+00:00",
  "user_goal": "Create a wiki test entry.",
  "route_mode": "cloud",
  "model_used": "gpt-test",
  "cloud_model": "gpt-test",
  "codex_model": "codex-test",
  "result_status": "completed",
  "value_score": 0.91,
  "postmortem": "",
  "tags": [],
  "metadata": {},
  "message_count": 2,
  "tool_call_count": 1,
  "file_change_count": 1
}
""",
        "utf-8",
    )
    (task_dir / "tool_trace.json").write_text(
        """{
  "task_id": "task-1",
  "session_id": "task-1",
  "tool_calls": [
    {"tool": "apply_patch", "output_summary": "Updated the wiki."}
  ],
  "files_changed": ["docs/example.md"]
}
""",
        "utf-8",
    )
    (task_dir / "file_changes.json").write_text(
        """{
  "task_id": "task-1",
  "session_id": "task-1",
  "file_changes": [
    {"path": "docs/example.md", "change_type": "created", "summary": "Created example page."}
  ]
}
""",
        "utf-8",
    )
    (task_dir / "conversation.jsonl").write_text(
        '{"role":"user","source":"user","content":"Create a wiki test entry."}\n'
        '{"role":"assistant","source":"codex","content":"Done."}\n',
        "utf-8",
    )
    (task_dir / "notes.md").write_text("Wiki builder note.", "utf-8")

    wiki_root = tmp_path / "wiki"
    written_paths = build_wiki(task_runs_root, wiki_root)

    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "tasks" / "task-1.md").exists()
    assert len(written_paths) == 3
