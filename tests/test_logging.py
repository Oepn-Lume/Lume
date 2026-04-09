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
    ShadowSessionRecorder,
    ShadowToolCall,
    write_shadow_log,
)
from lume.execution.runtime import ObservedRuntime, RuntimeModels


def test_write_shadow_log_creates_expected_files(tmp_path: Path) -> None:
    record = ShadowLogRecord(
        task_id="task-0001",
        user_goal="Create the first shadow log record.",
        route_mode="cloud",
        model_used="gpt-test",
        session_id="session-0001",
        cloud_model="gpt-test",
        codex_model="codex-test",
        messages=[
            ShadowMessage(role="user", content="Prompt A", source="user"),
            ShadowMessage(
                role="assistant",
                content="Cloud thinks we should patch file X.",
                source="cloud",
                model="gpt-test",
            ),
            ShadowMessage(
                role="assistant",
                content="Response A",
                source="codex",
                model="codex-test",
            ),
        ],
        tool_calls=[
            ShadowToolCall(tool="apply_patch", status="ok", output_summary="patched")
        ],
        file_changes=[
            ShadowFileChange(
                path="docs/example.md",
                change_type="created",
                summary="Created example document.",
            )
        ],
        result_status="completed",
        value_score=0.9,
        postmortem="No issues.",
        notes="Stored as a smoke test.",
        tags=["shadow", "smoke"],
    )

    task_dir = write_shadow_log(record, tmp_path)

    assert task_dir == tmp_path / "task-0001"
    assert (task_dir / "task.json").exists()
    assert (task_dir / "prompt_response.json").exists()
    assert (task_dir / "conversation.jsonl").exists()
    assert (task_dir / "tool_trace.json").exists()
    assert (task_dir / "file_changes.json").exists()
    assert (task_dir / "file_diff_summary.md").exists()
    assert (task_dir / "outcome.json").exists()
    assert (task_dir / "manifest.json").exists()
    assert (task_dir / "notes.md").exists()
    assert (tmp_path / "session_index.json").exists()

    task_payload = json.loads((task_dir / "task.json").read_text("utf-8"))
    assert task_payload["task_id"] == "task-0001"
    assert task_payload["route_mode"] == "cloud"
    assert task_payload["message_count"] == 3

    prompt_payload = json.loads(
        (task_dir / "prompt_response.json").read_text("utf-8")
    )
    assert prompt_payload["pairs"][0]["prompt"] == "Prompt A"
    assert prompt_payload["pairs"][0]["response"] == "Cloud thinks we should patch file X."

    conversation_lines = (task_dir / "conversation.jsonl").read_text("utf-8").strip()
    conversation_payloads = [
        json.loads(line) for line in conversation_lines.splitlines() if line.strip()
    ]
    assert conversation_payloads[1]["source"] == "cloud"
    assert conversation_payloads[2]["source"] == "codex"

    notes = (task_dir / "notes.md").read_text("utf-8")
    assert "Create the first shadow log record." in notes
    assert "Stored as a smoke test." in notes


def test_write_shadow_log_handles_empty_changes(tmp_path: Path) -> None:
    record = ShadowLogRecord(
        task_id="task-0002",
        user_goal="Write a log even when nothing changed.",
        route_mode="local",
        model_used="gemma-test",
        messages=[
            ShadowMessage(role="user", content="Nothing changed.", source="user")
        ],
    )

    task_dir = write_shadow_log(record, tmp_path)

    summary = (task_dir / "file_diff_summary.md").read_text("utf-8")
    assert "No files changed" in summary


def test_session_index_is_updated_for_multiple_sessions(tmp_path: Path) -> None:
    first = ShadowLogRecord(
        task_id="task-1",
        user_goal="First task",
        route_mode="cloud",
        model_used="gpt-a",
        messages=[ShadowMessage(role="user", content="First", source="user")],
    )
    second = ShadowLogRecord(
        task_id="task-2",
        user_goal="Second task",
        route_mode="local",
        model_used="gemma-b",
        messages=[ShadowMessage(role="user", content="Second", source="user")],
    )

    write_shadow_log(first, tmp_path)
    write_shadow_log(second, tmp_path)

    session_index = json.loads((tmp_path / "session_index.json").read_text("utf-8"))
    assert len(session_index["sessions"]) == 2
    assert {entry["task_id"] for entry in session_index["sessions"]} == {
        "task-1",
        "task-2",
    }


def test_shadow_session_recorder_flushes_live_session(tmp_path: Path) -> None:
    recorder = ShadowSessionRecorder(
        task_id="live-session",
        user_goal="Capture a runtime conversation.",
        route_mode="hybrid",
        model_used="gpt-live",
        output_root=tmp_path,
        cloud_model="gpt-live",
        codex_model="codex-live",
        metadata={"thread_id": "thread-123"},
    )

    recorder.add_user_message("Need the runtime to capture everything.")
    recorder.add_cloud_message(
        "Cloud generated a plan.",
        message_type="reasoning",
    )
    recorder.add_codex_message("Codex is applying the patch.")
    recorder.add_tool_call(
        tool="apply_patch",
        output_summary="Updated the logging module.",
        arguments={"file": "src/lume/logging/shadow.py"},
    )
    recorder.add_file_change(
        path="src/lume/logging/shadow.py",
        summary="Added session-level logging support.",
    )
    recorder.finalize(
        result_status="completed",
        value_score=0.97,
        notes="Live recorder smoke test.",
    )

    task_dir = recorder.flush()
    task_payload = json.loads((task_dir / "task.json").read_text("utf-8"))
    conversation_lines = (task_dir / "conversation.jsonl").read_text("utf-8").splitlines()

    assert task_payload["message_count"] == 3
    assert task_payload["tool_call_count"] == 1
    assert task_payload["metadata"]["thread_id"] == "thread-123"
    assert len(conversation_lines) == 3


def test_observed_runtime_records_without_manual_logger_calls(tmp_path: Path) -> None:
    runtime = ObservedRuntime(
        task_id="observed-runtime",
        user_goal="Verify no-touch runtime logging.",
        route_mode="hybrid",
        output_root=tmp_path,
        models=RuntimeModels(
            primary="gpt-primary",
            cloud="gpt-cloud",
            codex="codex-local",
        ),
        cloud_handler=lambda prompt: f"cloud::{prompt}",
        codex_handler=lambda instruction: f"codex::{instruction}",
        metadata={"mode": "demo"},
    )

    runtime.user("Handle the task invisibly.")
    plan = runtime.cloud.complete("plan next step", message_type="reasoning")
    runtime.codex.respond(plan, message_type="execution")
    runtime.codex.tool("shell_command", output_summary="listed files")
    runtime.codex.file(
        "src/lume/execution/runtime.py",
        summary="Observed runtime verified.",
    )
    task_dir = runtime.finish(result_status="completed", value_score=0.91)

    task_payload = json.loads((task_dir / "task.json").read_text("utf-8"))
    conversation_lines = (task_dir / "conversation.jsonl").read_text("utf-8").splitlines()

    assert task_payload["message_count"] == 4
    assert task_payload["tool_call_count"] == 1
    assert task_payload["file_change_count"] == 1
    assert task_payload["metadata"]["mode"] == "demo"
    assert any("\"source\": \"cloud\"" in line for line in conversation_lines)
    assert any("\"source\": \"codex\"" in line for line in conversation_lines)
