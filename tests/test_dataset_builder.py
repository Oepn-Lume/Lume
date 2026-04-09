from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill import build_distill_datasets


def test_build_distill_datasets_creates_expected_files(tmp_path: Path) -> None:
    task_dir = tmp_path / "task_runs" / "task-1"
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(
        """{
  "task_id": "task-1",
  "route_mode": "cloud",
  "user_goal": "Write a concise summary",
  "model_used": "gpt-test",
  "result_status": "completed",
  "value_score": 0.9,
  "message_count": 2,
  "tool_call_count": 1,
  "file_change_count": 0
}
""",
        "utf-8",
    )
    (task_dir / "prompt_response.json").write_text(
        """{
  "pairs": [{"prompt": "Summarize this", "response": "Done."}]
}
""",
        "utf-8",
    )
    (task_dir / "tool_trace.json").write_text(
        """{
  "tool_calls": [{"tool": "apply_patch", "output_summary": "Patched a file."}]
}
""",
        "utf-8",
    )
    (task_dir / "notes.md").write_text("A useful task note.", "utf-8")
    raw_logs = tmp_path / "raw_logs"
    raw_logs.mkdir()
    (raw_logs / "current-thread-training.jsonl").write_text(
        '{"timestamp":"2026-04-09T00:00:00+00:00","role":"user","source":"thread","content":"hello"}\n'
        '{"timestamp":"2026-04-09T00:00:01+00:00","role":"assistant","source":"thread","content":"world"}\n',
        "utf-8",
    )
    (raw_logs / "codex-session-import.jsonl").write_text(
        '{"timestamp":"2026-04-09T00:00:02+00:00","role":"user","source":"codex_response_item","content":"question","session_file":"x"}\n'
        '{"timestamp":"2026-04-09T00:00:03+00:00","role":"assistant","source":"codex_response_item","content":"answer","session_file":"x"}\n',
        "utf-8",
    )

    written = build_distill_datasets(
        tmp_path / "task_runs",
        tmp_path / "datasets",
        raw_logs,
    )
    assert len(written) == 4
    for path in written:
        assert path.exists()
