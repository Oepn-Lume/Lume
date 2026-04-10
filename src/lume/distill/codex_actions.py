"""Build Codex action-taxonomy datasets from session comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lume.codex import classify_codex_action


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _trim(text: str, limit: int = 220) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def build_codex_action_dataset(reports_root: Path, datasets_root: Path) -> list[Path]:
    """Build action-oriented SFT/eval datasets for Codex-like software work."""

    datasets_root.mkdir(parents=True, exist_ok=True)
    comparison_json = reports_root / "gemma_vs_cloud_all_sessions.json"
    output_sft = datasets_root / "codex_action_sft.jsonl"
    output_eval = datasets_root / "codex_action_eval.jsonl"
    action_eval_outputs = {
        "continue_task": datasets_root / "codex_continue_eval.jsonl",
        "prepare_patch": datasets_root / "codex_patch_eval.jsonl",
        "inspect_log": datasets_root / "codex_log_eval.jsonl",
    }

    if not comparison_json.exists():
        output_sft.write_text("", "utf-8")
        output_eval.write_text("", "utf-8")
        for path in action_eval_outputs.values():
            path.write_text("", "utf-8")
        return [output_sft, output_eval, *action_eval_outputs.values()]

    comparison_payload = _read_json(comparison_json)
    comparisons = comparison_payload.get("comparisons", [])
    if not isinstance(comparisons, list):
        comparisons = []

    sft_records: list[dict[str, Any]] = []
    eval_records: list[dict[str, Any]] = []
    action_eval_records: dict[str, list[dict[str, Any]]] = {key: [] for key in action_eval_outputs}

    for item in comparisons:
        if not isinstance(item, dict):
            continue
        comparison_id = str(item.get("comparison_id", "")).strip()
        user_text = str(item.get("user_text", "")).strip()
        cloud_text = str(item.get("cloud_text", "")).strip()
        gemma_text = str(item.get("gemma_text", "")).strip()
        prompt_role = str(item.get("prompt_role", "")).strip() or "user"
        if not comparison_id or not user_text or not cloud_text:
            continue

        action = classify_codex_action(user_text)
        input_text = "\n".join(
            [
                f"Prompt_Role: {prompt_role}",
                f"Current_Request: {user_text}",
                f"Task: identify the most likely Codex worksite action and continue with the next useful step.",
            ]
        ).strip()
        target_payload = {
            "action_label": action.action_label,
            "action_family": action.action_family,
            "response_style": "action_first" if action.short_action else "contextual",
            "ideal_reply": _trim(cloud_text, 260),
        }
        metadata = {
            "source": "codex_action_taxonomy",
            "prompt_role": prompt_role,
            "comparison_id": comparison_id,
            "short_action": action.short_action,
            "cloud_char_len": item.get("metrics", {}).get("cloud_char_len"),
            "gemma_char_len": item.get("metrics", {}).get("gemma_char_len"),
            "similarity": item.get("metrics", {}).get("similarity"),
        }
        sft_records.append(
            {
                "task_id": f"{comparison_id}-codex-action",
                "input": input_text,
                "target": target_payload,
                "metadata": metadata,
            }
        )
        eval_records.append(
            {
                "task_id": f"{comparison_id}-codex-action-eval",
                "input": input_text,
                "target": {
                    "action_label": action.action_label,
                    "ideal_reply": _trim(cloud_text, 180),
                },
                "metadata": {
                    **metadata,
                    "gemma_reply": _trim(gemma_text, 180),
                },
            }
        )
        if action.action_label in action_eval_records:
            action_eval_records[action.action_label].append(eval_records[-1])

    for path, records in [(output_sft, sft_records), (output_eval, eval_records)]:
        path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
            "utf-8",
        )
    for action_label, path in action_eval_outputs.items():
        records = action_eval_records[action_label]
        path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""),
            "utf-8",
        )
    return [output_sft, output_eval, *action_eval_outputs.values()]
