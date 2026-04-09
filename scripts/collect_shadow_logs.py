"""CLI entrypoint for collecting task traces into shadow logs."""

from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.logging import (
    ShadowFileChange,
    ShadowLogRecord,
    ShadowMessage,
    ShadowToolCall,
    write_shadow_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id")
    parser.add_argument("--user-goal")
    parser.add_argument("--session-id")
    parser.add_argument("--route-mode", default="cloud")
    parser.add_argument("--model-used", default="unknown")
    parser.add_argument("--cloud-model")
    parser.add_argument("--codex-model", default="codex")
    parser.add_argument("--prompt", action="append", default=[])
    parser.add_argument("--response", action="append", default=[])
    parser.add_argument("--message", action="append", default=[])
    parser.add_argument("--tool-call", action="append", default=[])
    parser.add_argument("--file-changed", action="append", default=[])
    parser.add_argument("--file-change", action="append", default=[])
    parser.add_argument("--result-status", default="completed")
    parser.add_argument("--value-score", type=float, default=0.0)
    parser.add_argument("--postmortem", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--metadata-json")
    parser.add_argument("--input-json")
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    return parser.parse_args()


def _coerce_dataclass(raw_items: list[str], cls: type) -> list[object]:
    allowed_fields = {field.name for field in fields(cls)}
    items: list[object] = []
    for raw_item in raw_items:
        payload = json.loads(raw_item)
        normalized = {
            key: value for key, value in payload.items() if key in allowed_fields
        }
        items.append(cls(**normalized))
    return items


def parse_messages(
    raw_messages: list[str],
    prompts: list[str],
    responses: list[str],
) -> list[ShadowMessage]:
    messages = list(_coerce_dataclass(raw_messages, ShadowMessage))
    if messages:
        return messages

    fallback_messages: list[ShadowMessage] = []
    for prompt in prompts:
        fallback_messages.append(
            ShadowMessage(role="user", content=prompt, source="user")
        )
    for response in responses:
        fallback_messages.append(
            ShadowMessage(role="assistant", content=response, source="codex")
        )
    return fallback_messages


def parse_metadata(raw_metadata: str | None) -> dict[str, object]:
    if not raw_metadata:
        return {}
    return json.loads(raw_metadata)


def build_record_from_payload(payload: dict[str, object]) -> ShadowLogRecord:
    messages = [
        ShadowMessage(**message)
        for message in payload.get("messages", [])
    ]
    tool_calls = [
        ShadowToolCall(**tool_call)
        for tool_call in payload.get("tool_calls", [])
    ]
    file_changes = [
        ShadowFileChange(**file_change)
        for file_change in payload.get("file_changes", [])
    ]
    return ShadowLogRecord(
        task_id=str(payload["task_id"]),
        user_goal=str(payload["user_goal"]),
        route_mode=str(payload.get("route_mode", "cloud")),
        model_used=str(payload.get("model_used", "unknown")),
        session_id=payload.get("session_id"),
        cloud_model=payload.get("cloud_model"),
        codex_model=payload.get("codex_model"),
        messages=messages,
        tool_calls=tool_calls,
        file_changes=file_changes,
        result_status=str(payload.get("result_status", "completed")),
        value_score=float(payload.get("value_score", 0.0)),
        postmortem=str(payload.get("postmortem", "")),
        notes=str(payload.get("notes", "")),
        tags=[str(tag) for tag in payload.get("tags", [])],
        metadata=dict(payload.get("metadata", {})),
        timestamp=str(payload.get("timestamp")) if payload.get("timestamp") else None,
    )


def build_record_from_args(args: argparse.Namespace) -> ShadowLogRecord:
    if not args.task_id or not args.user_goal:
        raise ValueError("--task-id and --user-goal are required without --input-json")

    tool_calls = [
        tool_call
        for tool_call in _coerce_dataclass(args.tool_call, ShadowToolCall)
    ]
    file_changes = [
        ShadowFileChange(path=path) for path in args.file_changed
    ] + [
        file_change
        for file_change in _coerce_dataclass(args.file_change, ShadowFileChange)
    ]
    return ShadowLogRecord(
        task_id=args.task_id,
        user_goal=args.user_goal,
        route_mode=args.route_mode,
        model_used=args.model_used,
        session_id=args.session_id,
        cloud_model=args.cloud_model,
        codex_model=args.codex_model,
        messages=parse_messages(args.message, args.prompt, args.response),
        tool_calls=tool_calls,
        file_changes=file_changes,
        result_status=args.result_status,
        value_score=args.value_score,
        postmortem=args.postmortem,
        notes=args.notes,
        tags=args.tag,
        metadata=parse_metadata(args.metadata_json),
    )


def main() -> None:
    args = parse_args()
    if args.input_json:
        payload = json.loads(Path(args.input_json).read_text("utf-8"))
        record = build_record_from_payload(payload)
    else:
        record = build_record_from_args(args)
    task_dir = write_shadow_log(record, args.output_root)
    print(task_dir)


if __name__ == "__main__":
    main()
