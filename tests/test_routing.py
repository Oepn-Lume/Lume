from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.routing import route_task


def test_route_task_returns_cloud_for_high_complexity(tmp_path: Path) -> None:
    config = tmp_path / "routing.yaml"
    config.write_text(
        'default_mode: "cloud"\n'
        'rules:\n'
        '  novel_complex_task: "cloud"\n'
        '  privacy_sensitive_task: "hybrid"\n'
        '  high_similarity_task: "local"\n'
        '  cloud_unavailable: "local"\n'
        'thresholds:\n'
        '  similarity_for_local: 0.85\n',
        "utf-8",
    )
    task_runs = tmp_path / "task_runs"
    task_runs.mkdir()
    decision = route_task(
        "Design a system architecture pipeline for a new memory stack",
        routing_config_path=config,
        task_runs_root=task_runs,
    )
    assert decision.mode == "cloud"


def test_route_task_returns_local_for_high_similarity(tmp_path: Path) -> None:
    config = tmp_path / "routing.yaml"
    config.write_text(
        'default_mode: "cloud"\n'
        'rules:\n'
        '  novel_complex_task: "cloud"\n'
        '  privacy_sensitive_task: "hybrid"\n'
        '  high_similarity_task: "local"\n'
        '  cloud_unavailable: "local"\n'
        'thresholds:\n'
        '  similarity_for_local: 0.2\n',
        "utf-8",
    )
    task_dir = tmp_path / "task_runs" / "task-1"
    task_dir.mkdir(parents=True)
    (task_dir / "task.json").write_text(
        '{"task_id":"task-1","user_goal":"write a short summary","timestamp":"2026-04-09T00:00:00+00:00"}',
        "utf-8",
    )
    decision = route_task(
        "write a short summary",
        routing_config_path=config,
        task_runs_root=tmp_path / "task_runs",
    )
    assert decision.mode == "local"
