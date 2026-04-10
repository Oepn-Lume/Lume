from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill.battery_cascade import build_battery_cascade_dataset


def test_build_battery_cascade_dataset_from_artifact(tmp_path: Path) -> None:
    task_runs_root = tmp_path / "task_runs"
    datasets_root = tmp_path / "datasets"
    task_dir = task_runs_root / "demo-task"
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir(parents=True)

    (task_dir / "task.json").write_text(
        json.dumps(
            {
                "task_id": "demo-task",
                "user_goal": "write a system architecture summary with python code",
                "route_mode": "hybrid",
                "value_score": 0.95,
            },
            ensure_ascii=False,
        ),
        "utf-8",
    )
    (artifacts_dir / "battery_dispatch.json").write_text(
        json.dumps(
            {
                "primary_expert": "base-expert",
                "selected_expert_count": 3,
                "candidate_scores": {
                    "base-expert": 0.55,
                    "code-expert": 0.43,
                    "logic-expert": 0.41,
                },
                "cascade_outputs": [
                    {
                        "step": 1,
                        "expert_name": "base-expert",
                        "domain": "general",
                        "matched_keywords": ["write", "summary"],
                        "output": "Base draft",
                    },
                    {
                        "step": 2,
                        "expert_name": "code-expert",
                        "domain": "code",
                        "matched_keywords": ["code", "python"],
                        "output": "Code refinement",
                    },
                    {
                        "step": 3,
                        "expert_name": "logic-expert",
                        "domain": "reasoning",
                        "matched_keywords": ["architecture", "system"],
                        "output": "Final integrated result",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        "utf-8",
    )

    output_path = build_battery_cascade_dataset(task_runs_root, datasets_root)
    lines = [line for line in output_path.read_text("utf-8").splitlines() if line.strip()]
    assert len(lines) == 4

    first = json.loads(lines[0])
    assert first["metadata"]["expert_name"] == "base-expert"
    assert first["metadata"]["selected_expert_count"] == 3

    final = json.loads(lines[-1])
    assert final["task_id"] == "demo-task-battery-cascade-final"
    assert final["target"] == "Final integrated result"
