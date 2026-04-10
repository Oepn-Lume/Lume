"""Builders for on-site alignment datasets derived from session comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lume.logging.codex_sessions import normalize_session_event


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _trim(text: str, limit: int = 220) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _build_prompt_variants(
    *,
    history_lines: list[str],
    internal_lines: list[str],
    current_state: str,
    user_text: str,
    prompt_role: str,
) -> list[tuple[str, str]]:
    history_short = history_lines[-3:] if history_lines else ["No prior session history found"]
    internal_short = internal_lines[-3:] if internal_lines else ["No recent internal events found"]
    variants: list[tuple[str, str]] = [
        (
            "full",
            "\n".join(
                [
                    "Session_History:",
                    *(history_lines or ["No prior session history found"]),
                    "",
                    "Internal_Events:",
                    *(internal_lines or ["No recent internal events found"]),
                    "",
                    "Current_State:",
                    current_state,
                    "",
                    f"Current_Request: {user_text}",
                    "",
                    "Task: continue the live task as an on-site teammate. Stay concise, stateful, and execution-aware.",
                ]
            ).strip(),
        ),
        (
            "compact",
            "\n".join(
                [
                    "Session_History:",
                    *history_short,
                    "",
                    "Internal_Events:",
                    *internal_short,
                    "",
                    f"Current_Request: {user_text}",
                    "",
                    "Task: continue the current work without resetting context.",
                ]
            ).strip(),
        ),
        (
            "action",
            "\n".join(
                [
                    "Current_State:",
                    current_state,
                    "",
                    "Recent_Internal_Events:",
                    *internal_short,
                    "",
                    f"Current_Request: {user_text}",
                    "",
                    "Task: choose the next on-site action. Prefer action over explanation.",
                ]
            ).strip(),
        ),
    ]
    if prompt_role == "developer":
        variants.append(
            (
                "developer_protocol",
                "\n".join(
                    [
                        "<internal_action>",
                        f"Current_State: {current_state}",
                        f"Developer_Command: {user_text}",
                        "Task: respond as an internal execution agent. Keep the reply extremely brief and action-oriented.",
                        "</internal_action>",
                    ]
                ).strip(),
            )
        )
    else:
        variants.append(
            (
                "short_command",
                "\n".join(
                    [
                        f"Current_Request: {user_text}",
                        f"Current_State: {current_state}",
                        "",
                        "Task: treat short commands as stateful continuations rather than new conversations.",
                    ]
                ).strip(),
            )
        )
    return variants


def _load_session_events(session_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in session_path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        normalized = normalize_session_event(record, session_path)
        if normalized is not None:
            events.append(normalized)
    return events


def _context_windows(
    comparison: dict[str, Any],
    *,
    supplemental_events: list[dict[str, Any]],
) -> tuple[list[str], list[str], str]:
    session_file = Path(str(comparison.get("session_file", "")))
    user_index = int(comparison.get("user_index", 0))
    assistant_index = int(comparison.get("assistant_index", 0))
    assistant_timestamp = str(comparison.get("assistant_timestamp", ""))

    history_lines: list[str] = []
    current_state = ""
    try:
        events = _load_session_events(session_file)
    except OSError:
        events = []

    current_user_counter = 0
    current_assistant_counter = 0
    for event in events:
        source = str(event.get("source", ""))
        role = str(event.get("role", "")).strip()
        content = str(event.get("content", "")).strip()
        if not content:
            continue
        if role in {"user", "developer"} and source == "codex_response_item":
            current_user_counter += 1
            current_assistant_counter = 0
        elif role == "assistant" and source == "codex_response_item":
            current_assistant_counter += 1
            if current_user_counter == user_index and current_assistant_counter == assistant_index:
                break
        label = role.upper() if role else "SYSTEM"
        history_lines.append(f"{label}: {_trim(content, 180)}")
    history_lines = history_lines[-6:]

    internal_lines: list[str] = []
    for event in supplemental_events:
        if str(event.get("session_file", "")) != str(session_file):
            continue
        if str(event.get("timestamp", "")) > assistant_timestamp:
            continue
        source = str(event.get("source", ""))
        if source not in {
            "codex_event:exec_command_end",
            "codex_event:patch_apply_end",
            "codex_response_item:function_call_output",
            "codex_event:agent_message",
        }:
            continue
        content = _trim(str(event.get("content", "")), 200)
        if source == "codex_event:exec_command_end" and not current_state:
            current_state = content
        internal_lines.append(f"{source}: {content}")
    internal_lines = internal_lines[-5:]
    return history_lines, internal_lines, current_state or "No current state snapshot"


def build_onsite_alignment_datasets(reports_root: Path, datasets_root: Path) -> list[Path]:
    """Build on-site alignment datasets from Gemma-vs-cloud comparison artifacts."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    comparison_json = reports_root / "gemma_vs_cloud_all_sessions.json"
    supplemental_jsonl = reports_root / "gemma_vs_cloud_all_sessions_supplemental_events.jsonl"

    output_alignment = datasets_root / "onsite_alignment_sft.jsonl"
    output_developer = datasets_root / "developer_chain_sft.jsonl"
    output_dpo = datasets_root / "onsite_alignment_dpo.jsonl"
    output_dpo_augmented = datasets_root / "onsite_alignment_dpo_3000.jsonl"

    if not comparison_json.exists():
        for path in [output_alignment, output_developer, output_dpo, output_dpo_augmented]:
            path.write_text("", "utf-8")
        return [output_alignment, output_developer, output_dpo, output_dpo_augmented]

    comparison_payload = _read_json(comparison_json)
    comparisons = comparison_payload.get("comparisons", [])
    if not isinstance(comparisons, list):
        comparisons = []
    supplemental_events = _read_jsonl(supplemental_jsonl)

    alignment_records: list[dict[str, Any]] = []
    developer_records: list[dict[str, Any]] = []
    dpo_records: list[dict[str, Any]] = []
    dpo_augmented_records: list[dict[str, Any]] = []

    for item in comparisons:
        if not isinstance(item, dict):
            continue
        user_text = str(item.get("user_text", "")).strip()
        cloud_text = str(item.get("cloud_text", "")).strip()
        gemma_text = str(item.get("gemma_text", "")).strip()
        prompt_role = str(item.get("prompt_role", "")).strip()
        comparison_id = str(item.get("comparison_id", "")).strip()
        if not user_text or not cloud_text or not comparison_id:
            continue

        history_lines, internal_lines, current_state = _context_windows(
            item,
            supplemental_events=supplemental_events,
        )
        variants = _build_prompt_variants(
            history_lines=history_lines,
            internal_lines=internal_lines,
            current_state=current_state,
            user_text=user_text,
            prompt_role=prompt_role,
        )
        input_text = variants[0][1]

        base_record = {
            "task_id": comparison_id,
            "input": input_text,
            "target": cloud_text,
            "metadata": {
                "source": "gemma_vs_cloud_comparison",
                "prompt_role": prompt_role,
                "session_file": item.get("session_file"),
                "session_id": item.get("session_id"),
                "user_index": item.get("user_index"),
                "assistant_index": item.get("assistant_index"),
                "assistant_phase": item.get("assistant_phase"),
                "cloud_char_len": item.get("metrics", {}).get("cloud_char_len"),
                "gemma_char_len": item.get("metrics", {}).get("gemma_char_len"),
                "similarity": item.get("metrics", {}).get("similarity"),
                "cloud_has_code": item.get("metrics", {}).get("cloud_has_code"),
                "gemma_has_code": item.get("metrics", {}).get("gemma_has_code"),
            },
        }
        alignment_records.append(base_record)

        if prompt_role == "developer":
            developer_records.append(
                {
                    **base_record,
                    "task_id": f"{comparison_id}-developer-chain",
                    "metadata": {
                        **base_record["metadata"],
                        "source": "developer_to_cloud_alignment",
                    },
                }
            )

        if gemma_text:
            base_metadata = {
                "source": "gemma_vs_cloud_preference",
                "prompt_role": prompt_role,
                "session_file": item.get("session_file"),
                "session_id": item.get("session_id"),
                "user_index": item.get("user_index"),
                "assistant_index": item.get("assistant_index"),
                "assistant_phase": item.get("assistant_phase"),
                "cloud_char_len": item.get("metrics", {}).get("cloud_char_len"),
                "gemma_char_len": item.get("metrics", {}).get("gemma_char_len"),
                "similarity": item.get("metrics", {}).get("similarity"),
                "cloud_has_code": item.get("metrics", {}).get("cloud_has_code"),
                "gemma_has_code": item.get("metrics", {}).get("gemma_has_code"),
            }
            dpo_records.append(
                {
                    "task_id": f"{comparison_id}-onsite-dpo",
                    "prompt": input_text,
                    "chosen": cloud_text,
                    "rejected": gemma_text,
                    "metadata": base_metadata,
                }
            )
            for variant_name, variant_prompt in variants:
                dpo_augmented_records.append(
                    {
                        "task_id": f"{comparison_id}-onsite-dpo-{variant_name}",
                        "prompt": variant_prompt,
                        "chosen": cloud_text,
                        "rejected": gemma_text,
                        "metadata": {
                            **base_metadata,
                            "source": "gemma_vs_cloud_preference_augmented",
                            "variant": variant_name,
                        },
                    }
                )

    for path, records in [
        (output_alignment, alignment_records),
        (output_developer, developer_records),
        (output_dpo, dpo_records),
        (output_dpo_augmented, dpo_augmented_records),
    ]:
        path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
            + ("\n" if records else ""),
            "utf-8",
        )
    return [output_alignment, output_developer, output_dpo, output_dpo_augmented]
