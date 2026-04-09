"""Import visible Codex desktop session logs into Lume raw logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def discover_session_files(*session_roots: Path) -> list[Path]:
    """Return Codex session jsonl files sorted by modified time across roots."""
    files: list[Path] = []
    seen: set[str] = set()
    for sessions_root in session_roots:
        if not sessions_root.exists():
            continue
        for path in sessions_root.rglob("*.jsonl"):
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            files.append(path)
    files.sort(key=lambda path: path.stat().st_mtime)
    return files


def _extract_text_from_content_items(content_items: list[dict[str, Any]]) -> str:
    texts: list[str] = []
    for item in content_items:
        text = item.get("text")
        if text:
            texts.append(str(text))
    return "\n".join(texts).strip()


def normalize_session_event(record: dict[str, Any], session_path: Path) -> dict[str, Any] | None:
    """Normalize a single Codex session event into training-log friendly JSON."""
    event_type = record.get("type")
    timestamp = record.get("timestamp")
    payload = record.get("payload", {})

    if event_type == "session_meta":
        return {
            "timestamp": timestamp,
            "role": "system",
            "source": "codex_session_meta",
            "content": json.dumps(payload, ensure_ascii=False),
            "raw_payload": payload,
            "session_file": str(session_path),
            "tags": ["codex-session", "meta"],
        }

    if event_type == "turn_context":
        return {
            "timestamp": timestamp,
            "role": "system",
            "source": "codex_turn_context",
            "content": json.dumps(payload, ensure_ascii=False),
            "raw_payload": payload,
            "session_file": str(session_path),
            "tags": ["codex-session", "context"],
        }

    if event_type == "event_msg":
        return {
            "timestamp": timestamp,
            "role": "system",
            "source": f"codex_event:{payload.get('type', 'unknown')}",
            "content": json.dumps(payload, ensure_ascii=False),
            "raw_payload": payload,
            "session_file": str(session_path),
            "tags": ["codex-session", "event"],
        }

    if event_type == "response_item":
        response_type = payload.get("type")
        if response_type == "message":
            content = _extract_text_from_content_items(payload.get("content", []))
            return {
                "timestamp": timestamp,
                "role": payload.get("role", "assistant"),
                "source": "codex_response_item",
                "content": content,
                "raw_payload": payload,
                "session_file": str(session_path),
                "tags": ["codex-session", "response-item", "message"],
            }
        return {
            "timestamp": timestamp,
            "role": "system",
            "source": f"codex_response_item:{response_type}",
            "content": json.dumps(payload, ensure_ascii=False),
            "raw_payload": payload,
            "session_file": str(session_path),
            "tags": ["codex-session", "response-item", str(response_type)],
        }

    return None


def _read_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {"files": {}}
    try:
        return json.loads(state_path.read_text("utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}


def _write_state(state_path: Path, payload: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def import_codex_sessions_incremental(
    sessions_root: Path,
    output_path: Path,
    state_path: Path,
    *,
    archived_root: Path | None = None,
) -> dict[str, int]:
    """Append only new Codex session events to the raw log."""
    session_files = discover_session_files(
        sessions_root,
        archived_root if archived_root is not None else Path(),
    )
    state = _read_state(state_path)
    file_state: dict[str, int] = dict(state.get("files", {}))

    new_lines: list[str] = []
    imported_records = 0
    scanned_files = 0

    for session_path in session_files:
        scanned_files += 1
        session_key = str(session_path)
        lines = session_path.read_text("utf-8").splitlines()
        start_index = int(file_state.get(session_key, 0))
        if start_index >= len(lines):
            file_state[session_key] = len(lines)
            continue
        for line in lines[start_index:]:
            if not line.strip():
                continue
            record = json.loads(line)
            normalized = normalize_session_event(record, session_path)
            if normalized is None:
                continue
            new_lines.append(json.dumps(normalized, ensure_ascii=False))
            imported_records += 1
        file_state[session_key] = len(lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if new_lines:
        with output_path.open("a", encoding="utf-8") as handle:
            for line in new_lines:
                handle.write(line + "\n")

    _write_state(
        state_path,
        {
            "files": file_state,
            "scanned_files": scanned_files,
            "imported_records": imported_records,
        },
    )
    return {
        "scanned_files": scanned_files,
        "imported_records": imported_records,
    }


def import_codex_sessions(
    sessions_root: Path,
    output_path: Path,
    *,
    latest_only: bool = False,
    archived_root: Path | None = None,
) -> int:
    """Import Codex session logs into a flat JSONL file."""
    session_files = discover_session_files(
        sessions_root,
        archived_root if archived_root is not None else Path(),
    )
    if latest_only and session_files:
        session_files = [session_files[-1]]

    normalized_records: list[str] = []
    for session_path in session_files:
        for line in session_path.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            normalized = normalize_session_event(record, session_path)
            if normalized is None:
                continue
            normalized_records.append(json.dumps(normalized, ensure_ascii=False))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(normalized_records) + ("\n" if normalized_records else ""),
        "utf-8",
    )
    return len(normalized_records)
