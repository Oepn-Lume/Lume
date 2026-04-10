from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.codex import classify_codex_action, codex_action_readiness_key
from lume.distill.codex_actions import build_codex_action_dataset


def test_classify_codex_action_labels_continue() -> None:
    decision = classify_codex_action("continue")
    assert decision.action_label == "continue_task"
    assert decision.short_action is True


def test_build_codex_action_dataset(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    reports_root.mkdir(parents=True)
    (reports_root / "gemma_vs_cloud_all_sessions.json").write_text(
        '{"comparisons":[{"comparison_id":"cmp-1","user_text":"publish","cloud_text":"Push the branch and create the release note.","gemma_text":"Here is a broad explanation of how publishing usually works.","prompt_role":"user","metrics":{"cloud_char_len":55,"gemma_char_len":84,"similarity":0.08}}]}',
        "utf-8",
    )
    output_sft, output_eval, continue_eval, patch_eval, log_eval = build_codex_action_dataset(reports_root, tmp_path / "datasets")
    sft_text = output_sft.read_text("utf-8")
    eval_text = output_eval.read_text("utf-8")
    assert "publish_release" in sft_text
    assert "action_first" in sft_text
    assert "publish_release" in eval_text
    assert continue_eval.read_text("utf-8") == ""
    assert patch_eval.read_text("utf-8") == ""
    assert log_eval.read_text("utf-8") == ""


def test_codex_action_readiness_key_maps_action_labels() -> None:
    assert codex_action_readiness_key("continue_task") == "continue_action_readiness"
    assert codex_action_readiness_key("prepare_patch") == "patch_action_readiness"
    assert codex_action_readiness_key("inspect_log") == "log_action_readiness"
    assert codex_action_readiness_key("publish_release") is None
