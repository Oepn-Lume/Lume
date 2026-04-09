"""Clean raw dialogue logs into trainable SFT examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text: str | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "cp936", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return []
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _is_trainable_message(record: dict[str, Any]) -> bool:
    role = record.get("role")
    source = str(record.get("source", ""))
    content = str(record.get("content", "")).strip()
    if not content:
        return False
    if role not in {"user", "assistant"}:
        return False
    if source.startswith("codex_response_item:reasoning"):
        return False
    if source.startswith("codex_event:"):
        return False
    if source in {"codex_session_meta", "codex_turn_context"}:
        return False
    if source == "codex_response_item" and content.startswith("<environment_context>"):
        return False
    if content.startswith("<environment_context>"):
        return False
    if content.startswith("<subagent_notification>"):
        return False
    return True


def _is_control_user_message(content: str) -> bool:
    return content.startswith("<environment_context>") or content.startswith("<subagent_notification>")


def _is_real_codex_record(record: dict[str, Any]) -> bool:
    source = str(record.get("source", ""))
    metadata = record.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("source") == "codex_session_import":
        return True
    return source.startswith("codex_")


def _is_full_fidelity_codex_record(record: dict[str, Any]) -> bool:
    source = str(record.get("source", ""))
    if source.startswith("codex_response_item"):
        return True
    return source in {
        "codex_event:agent_message",
        "codex_event:exec_command_end",
        "codex_event:patch_apply_end",
        "codex_event:web_search_end",
    }


def _stringify_target(record: dict[str, Any]) -> str:
    raw_payload = record.get("raw_payload")
    if raw_payload is not None:
        return json.dumps(raw_payload, ensure_ascii=False)
    target = str(record.get("content", "")).strip()
    return target


def _build_full_fidelity_codex_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    latest_user_by_session: dict[str, str] = {}
    turn_index = 0
    for record in records:
        session_file = str(record.get("session_file", ""))
        role = record.get("role")
        content = str(record.get("content", "")).strip()
        if role == "user" and content and not content.startswith("<"):
            latest_user_by_session[session_file] = content
            continue
        if not _is_full_fidelity_codex_record(record):
            continue
        target = _stringify_target(record).strip()
        if not target:
            continue
        latest_user = latest_user_by_session.get(session_file, "")
        built.append(
            {
                "task_id": f"codex-full-fidelity-{turn_index}",
                "input": latest_user or "[no-user-context-available]",
                "target": target,
                "metadata": {
                    "source": "codex_full_fidelity",
                    "record_source": record.get("source"),
                    "timestamp": record.get("timestamp"),
                    "session_file": session_file,
                },
            }
        )
        turn_index += 1
    return built


def _is_bootstrap_record(record: dict[str, Any]) -> bool:
    source = str(record.get("source", ""))
    return source in {
        "codex_session_meta",
        "codex_turn_context",
        "codex_response_item",
        "codex_response_item:reasoning",
        "codex_event:task_started",
        "codex_event:agent_message",
    }


def _build_bootstrap_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    records_by_session: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        session_file = str(record.get("session_file", ""))
        records_by_session.setdefault(session_file, []).append(record)

    bootstrap_index = 0
    for session_file, session_records in records_by_session.items():
        environment_context = ""
        for record in session_records:
            role = record.get("role")
            content = str(record.get("content", "")).strip()
            if role == "user" and content:
                if _is_control_user_message(content):
                    if content.startswith("<environment_context>"):
                        environment_context = content
                    continue
                break
            if not _is_bootstrap_record(record):
                continue
            target = _stringify_target(record).strip()
            if not target:
                continue
            input_parts = [
                "Bootstrap phase before the first real user task.",
                f"Session file: {session_file}",
            ]
            if environment_context:
                input_parts.append(environment_context)
            built.append(
                {
                    "task_id": f"codex-bootstrap-{bootstrap_index}",
                    "input": "\n".join(input_parts),
                    "target": target,
                    "metadata": {
                        "source": "codex_bootstrap",
                        "record_source": record.get("source"),
                        "timestamp": record.get("timestamp"),
                        "session_file": session_file,
                    },
                }
            )
            bootstrap_index += 1
    return built


def _build_adjacent_pairs(
    records: list[dict[str, Any]],
    *,
    task_prefix: str,
    metadata_builder: Any,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for index in range(len(records) - 1):
        current_record = records[index]
        next_record = records[index + 1]
        if current_record.get("role") != "user":
            continue
        if next_record.get("role") != "assistant":
            continue
        current_session = current_record.get("session_file")
        next_session = next_record.get("session_file")
        if current_session and next_session and current_session != next_session:
            continue
        pairs.append(
            {
                "task_id": f"{task_prefix}-{index}",
                "input": current_record.get("content", ""),
                "target": next_record.get("content", ""),
                "metadata": metadata_builder(current_record, next_record),
            }
        )
    return pairs


def build_raw_dialogue_dataset(raw_logs_root: Path, datasets_root: Path) -> Path:
    """Build a simple dialogue SFT dataset from imported raw logs."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    output_path = datasets_root / "raw_dialogue_sft.jsonl"
    real_cloud_output_path = datasets_root / "real_cloud_dialogue_sft.jsonl"
    full_fidelity_output_path = datasets_root / "real_cloud_full_fidelity_sft.jsonl"
    bootstrap_output_path = datasets_root / "real_cloud_bootstrap_sft.jsonl"

    records: list[dict[str, Any]] = []

    codex_import_path = raw_logs_root / "codex-session-import.jsonl"
    imported_records = _read_jsonl(codex_import_path)
    trainable_records = [record for record in imported_records if _is_trainable_message(record)]
    codex_pairs = _build_adjacent_pairs(
        trainable_records,
        task_prefix="codex-session",
        metadata_builder=lambda current_record, next_record: {
            "source": "codex_session_import",
            "user_source": current_record.get("source"),
            "assistant_source": next_record.get("source"),
            "timestamp": next_record.get("timestamp"),
            "session_file": next_record.get("session_file"),
        },
    )
    records.extend(codex_pairs)

    thread_log_path = raw_logs_root / "current-thread-training.jsonl"
    thread_records = _read_jsonl(thread_log_path)
    thread_pairs = _build_adjacent_pairs(
        thread_records,
        task_prefix="thread-log",
        metadata_builder=lambda _current_record, next_record: {
            "source": "current_thread_training",
            "timestamp": next_record.get("timestamp"),
        },
    )
    records.extend(thread_pairs)

    output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )

    real_cloud_records = [record for record in records if _is_real_codex_record(record)]
    real_cloud_output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in real_cloud_records)
        + ("\n" if real_cloud_records else ""),
        "utf-8",
    )

    full_fidelity_records = _build_full_fidelity_codex_records(imported_records)
    full_fidelity_output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in full_fidelity_records)
        + ("\n" if full_fidelity_records else ""),
        "utf-8",
    )

    bootstrap_records = _build_bootstrap_records(imported_records)
    bootstrap_output_path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in bootstrap_records)
        + ("\n" if bootstrap_records else ""),
        "utf-8",
    )
    return output_path
