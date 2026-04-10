from pathlib import Path

from lume.spi import build_sar_protocol_dataset


def test_build_sar_protocol_dataset(tmp_path: Path) -> None:
    task_runs_root = tmp_path / "task_runs"
    task_dir = task_runs_root / "demo-task"
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(
        '{"task_id":"demo-task","timestamp":"2026-04-10T00:00:00+00:00","user_goal":"debug code","route_mode":"hybrid","model_used":"hybrid","result_status":"completed","value_score":0.95,"message_count":2,"tool_call_count":1,"file_change_count":1,"output_source":"hybrid","metadata":{"routing_reasons":["low complexity"],"planning_strategy":"hybrid"}}\n',
        "utf-8",
    )
    (task_dir / "tool_trace.json").write_text(
        '{"tool_calls":[{"tool":"battery_matrix_dispatch","source":"codex","output_summary":"Selected local experts","arguments":{"confidence":0.8}}]}\n',
        "utf-8",
    )
    (task_dir / "file_changes.json").write_text(
        '{"file_changes":[{"path":"src/demo.py","change_type":"modified","summary":"demo"}]}\n',
        "utf-8",
    )
    (task_dir / "outcome.json").write_text('{"result_status":"completed"}\n', "utf-8")

    output = build_sar_protocol_dataset(task_runs_root, tmp_path / "datasets")
    text = output.read_text("utf-8")
    assert "demo-task-sar" in text
    assert '"protocol": "sar-v1"' in text
    assert '"agent_type": "software-agent"' in text
