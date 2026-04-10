from pathlib import Path

from lume.charging import DeviceState, build_shadow_charge_ledger, evaluate_charging_window


def test_evaluate_charging_window_requires_idle_and_charging() -> None:
    state = DeviceState(hour=23, idle_minutes=45, is_charging=True, cpu_percent=8.0, gpu_busy=False)
    decision = evaluate_charging_window(state)
    assert decision.should_charge is True


def test_evaluate_charging_window_blocks_busy_device() -> None:
    state = DeviceState(hour=14, idle_minutes=5, is_charging=False, cpu_percent=70.0, gpu_busy=True)
    decision = evaluate_charging_window(state)
    assert decision.should_charge is False
    assert "outside charging window" in decision.reasons


def test_build_shadow_charge_ledger_collects_task_runs(tmp_path: Path) -> None:
    task_runs_root = tmp_path / "task_runs"
    task_dir = task_runs_root / "demo-task"
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(
        '{"task_id":"demo-task","timestamp":"2026-04-10T00:00:00+00:00","user_goal":"demo","route_mode":"hybrid","model_used":"cloud","result_status":"completed","value_score":0.95,"message_count":2,"tool_call_count":1,"file_change_count":1,"output_source":"hybrid"}\n',
        "utf-8",
    )
    (task_dir / "tool_trace.json").write_text(
        '{"tool_calls":[{"tool":"apply_patch"}]}\n',
        "utf-8",
    )
    (task_dir / "file_changes.json").write_text(
        '{"file_changes":[{"path":"src/demo.py","change_type":"modified","summary":"demo"}]}\n',
        "utf-8",
    )
    (task_dir / "outcome.json").write_text('{"result_status":"completed"}\n', "utf-8")
    (task_dir / "manifest.json").write_text('{"artifacts":{"task":"task.json"}}\n', "utf-8")

    written = build_shadow_charge_ledger(task_runs_root, tmp_path / "distilled" / "shadow_charge")
    assert len(written) == 2
    ledger_text = written[0].read_text("utf-8")
    assert "demo-task" in ledger_text
