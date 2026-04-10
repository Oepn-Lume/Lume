from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.rl.reward_dataset import build_rlef_datasets


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def test_build_rlef_datasets_tracks_energy_and_alignment(tmp_path: Path) -> None:
    task_dir = tmp_path / "continue-pipeline-demo"
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir(parents=True)

    _write_json(
        task_dir / "task.json",
        {
            "task_id": "continue-pipeline-demo",
            "user_goal": "continue",
            "route_mode": "hybrid",
            "value_score": 0.9,
            "tool_call_count": 1,
            "file_change_count": 1,
        },
    )
    _write_json(
        task_dir / "outcome.json",
        {
            "result_status": "completed",
            "value_score": 0.9,
        },
    )
    _write_json(
        task_dir / "tool_trace.json",
        {
            "tool_calls": [
                {
                    "tool": "apply_patch",
                    "status": "completed",
                    "output_summary": "Patched the runtime and tests.",
                    "arguments": {"file": "runtime.py"},
                }
            ]
        },
    )
    (task_dir / "conversation.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "role": "assistant",
                        "source": "cloud",
                        "message_type": "local_reasoning",
                        "content": "Please provide the article content before I continue.```python\nprint('demo')\n```",
                        "model": "gemma4:31b",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "role": "assistant",
                        "source": "cloud",
                        "message_type": "reasoning",
                        "content": "Apply the next patch and continue the current task.",
                        "model": "gpt-cloud-demo",
                        "metadata": {"hybrid": True},
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        "utf-8",
    )
    _write_json(
        artifacts_dir / "battery_dispatch.json",
        {
            "selected_expert_count": 3,
            "cascade_outputs": [],
        },
    )

    output_dir = tmp_path / "datasets"
    build_rlef_datasets(tmp_path, output_dir)

    reward_records = [
        json.loads(line)
        for line in (output_dir / "rlef_reward.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    task_record = next(record for record in reward_records if record["task_id"] == "continue-pipeline-demo")
    metadata = task_record["metadata"]
    assert metadata["action_task"] is True
    assert metadata["code_overproduction"] is True
    assert metadata["redundant_request"] is True
    assert metadata["energy_penalty"] > 0
    assert metadata["reward_align"] < metadata["reward_env"]

