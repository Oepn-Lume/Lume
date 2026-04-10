from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.onsite import build_dynamic_snapshot, format_field_report


def test_build_dynamic_snapshot_expands_short_command(tmp_path: Path) -> None:
    task_runs_root = tmp_path / "task_runs"
    latest_task = task_runs_root / "demo-task"
    latest_task.mkdir(parents=True)
    (latest_task / "task.json").write_text(
        '{"task_id":"demo-task","user_goal":"apply patch to build_distill.py"}',
        "utf-8",
    )
    (latest_task / "tool_trace.json").write_text(
        '{"tool_calls":[{"tool":"python","output_summary":"python test_route.py -> Success"}]}',
        "utf-8",
    )
    (latest_task / "file_changes.json").write_text(
        '{"file_changes":[{"path":"src/lume/distill/build_distill.py"}]}',
        "utf-8",
    )

    snapshot = build_dynamic_snapshot(
        "continue",
        task_runs_root=task_runs_root,
        workspace_root=tmp_path,
        sessions_root=tmp_path / "missing-sessions",
        archived_root=tmp_path / "missing-archived",
    )
    assert "Recent pending task: apply patch to build_distill.py" in snapshot.expanded_task
    assert snapshot.recent_file == "src/lume/distill/build_distill.py"
    report = format_field_report(snapshot)
    assert "<field_report>" in report
    assert "Current Focus: apply patch to build_distill.py" in report
