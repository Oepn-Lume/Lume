from pathlib import Path

import pytest

from lume.spi import (
    SAR_PROTOCOL_VERSION,
    ActionEnvelope,
    DomainType,
    RoboticsTraceAdapter,
    RewardEnvelope,
    SARAdapterRegistry,
    SARRecord,
    SoftwareTaskRunAdapter,
    StateEnvelope,
    build_sar_protocol_dataset,
)


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
    assert f'"protocol_version": "{SAR_PROTOCOL_VERSION}"' in text
    assert '"protocol": "sar-v1"' in text
    assert '"agent_type": "software-agent"' in text


def test_sar_record_validates_domain_and_protocol() -> None:
    state = StateEnvelope(
        domain=DomainType.SOFTWARE.value,
        world_snapshot={"task_id": "demo"},
        intent_trajectory=[],
        feedback_signals={},
    )
    action = ActionEnvelope(action_type="deliver_result", action_payload={})

    record = SARRecord(
        record_id="demo",
        agent_type="software-agent",
        state=state,
        action=action,
        reward=RewardEnvelope(total_reward=0.1),
    )

    assert record.protocol_version == SAR_PROTOCOL_VERSION


def test_sar_record_rejects_unknown_domain() -> None:
    with pytest.raises(ValueError):
        StateEnvelope(
            domain="unknown-domain",
            world_snapshot={},
            intent_trajectory=[],
            feedback_signals={},
        )


def test_default_software_adapter_supports_task_runs(tmp_path: Path) -> None:
    task_dir = tmp_path / "demo-task"
    task_dir.mkdir(parents=True)
    task_payload = {
        "task_id": "demo-task",
        "route_mode": "hybrid",
        "user_goal": "debug code",
        "result_status": "completed",
        "value_score": 0.9,
        "message_count": 2,
        "tool_call_count": 1,
        "file_change_count": 1,
        "metadata": {},
    }

    adapter = SoftwareTaskRunAdapter()
    assert adapter.supports(task_payload, task_dir)


def test_registry_returns_first_matching_adapter(tmp_path: Path) -> None:
    task_dir = tmp_path / "demo-task"
    task_dir.mkdir(parents=True)
    task_payload = {"route_mode": "hybrid"}
    registry = SARAdapterRegistry()
    adapter = SoftwareTaskRunAdapter()
    registry.register(adapter)

    assert registry.resolve(task_payload, task_dir) is adapter


def test_robotics_adapter_builds_motion_record(tmp_path: Path) -> None:
    task_dir = tmp_path / "robot-task"
    task_dir.mkdir(parents=True)
    (task_dir / "robot_trace.json").write_text(
        '{"environment":"warehouse-a","pose":{"x":1.2,"y":3.4},"sensors":{"lidar":"clear"},"motion_summary":{"path_efficiency":0.88,"collision_count":0,"energy_used":12.5,"latency_ms":120},"trace_steps":[{"step_index":1,"intent":"approach shelf","controller_mode":"assist","action":"move_to_pose","target_pose":{"x":2.0,"y":4.0},"confidence":0.81}],"result_status":"completed","executor":"robot-agent"}\n',
        "utf-8",
    )
    task_payload = {
        "task_id": "robot-task",
        "timestamp": "2026-04-10T00:00:00+00:00",
        "user_goal": "approach shelf",
        "domain": "robotics",
        "agent_type": "robot-agent",
        "result_status": "completed",
    }

    adapter = RoboticsTraceAdapter()
    assert adapter.supports(task_payload, task_dir)
    record = adapter.build_record(task_payload, task_dir)

    assert record.agent_type == "robot-agent"
    assert record.state.domain == "robotics"
    assert record.action.action_type == "motion_command"
    assert record.metadata["adapter"] == "robotics-trace"
