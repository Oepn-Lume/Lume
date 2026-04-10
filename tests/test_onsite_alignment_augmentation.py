from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.distill.onsite_alignment import build_onsite_alignment_datasets


def test_build_onsite_alignment_augmented_dpo(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    datasets_root = tmp_path / "datasets"
    reports_root.mkdir(parents=True)
    session_file = tmp_path / "session.jsonl"
    session_file.write_text("", "utf-8")
    (reports_root / "gemma_vs_cloud_all_sessions.json").write_text(
        json.dumps(
            {
                "comparisons": [
                    {
                        "comparison_id": "cmp-1",
                        "session_file": str(session_file),
                        "session_id": "s1",
                        "user_index": 1,
                        "assistant_index": 1,
                        "assistant_timestamp": "2026-04-10T00:00:00Z",
                        "user_text": "continue",
                        "cloud_text": "Apply the patch and run the next test.",
                        "gemma_text": "Please provide more details.",
                        "prompt_role": "user",
                        "assistant_phase": "commentary",
                        "metrics": {
                            "cloud_char_len": 39,
                            "gemma_char_len": 28,
                            "similarity": 0.05,
                            "cloud_has_code": False,
                            "gemma_has_code": False,
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        "utf-8",
    )
    (reports_root / "gemma_vs_cloud_all_sessions_supplemental_events.jsonl").write_text("", "utf-8")

    build_onsite_alignment_datasets(reports_root, datasets_root)
    augmented = datasets_root / "onsite_alignment_dpo_3000.jsonl"
    lines = [line for line in augmented.read_text("utf-8").splitlines() if line.strip()]
    assert len(lines) == 4
