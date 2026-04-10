from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.rl.grpo import _convert_group_records


def test_convert_group_records_flattens_best_vs_worst(tmp_path: Path) -> None:
    dataset_path = tmp_path / "onsite_alignment_grpo.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "task_id": "group-1",
                "prompt": "continue",
                "candidates": [
                    {"text": "Apply the patch and run tests.", "score": 1.4, "label": "chosen"},
                    {"text": "Please provide more details.", "score": 0.0, "label": "rejected"},
                ],
                "metadata": {"variant": "action"},
            },
            ensure_ascii=False,
        )
        + "\n",
        "utf-8",
    )
    records = _convert_group_records(dataset_path)
    assert len(records) == 1
    assert records[0]["chosen"] == "Apply the patch and run tests."
    assert records[0]["rejected"] == "Please provide more details."
    assert float(records[0]["weight"]) >= 1.0
