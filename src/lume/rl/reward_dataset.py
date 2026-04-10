"""Build reinforcement-learning style datasets from real task outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ACTION_KEYWORDS = {
    "continue",
    "publish",
    "fix",
    "implement",
    "retry",
    "next",
    "deploy",
    "debug",
    "repair",
    "ship",
    "继续",
    "发布",
    "修复",
    "实现",
    "重试",
    "下一步",
    "部署",
}
REDUNDANT_REQUEST_PATTERNS = (
    "please provide",
    "please share",
    "could you provide",
    "need more information",
    "请提供",
    "请发送",
    "需要更多信息",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _jsonl_write(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        + ("\n" if records else ""),
        "utf-8",
    )


def _tokenize(text: str) -> list[str]:
    return [token.strip(".,:;!?()[]{}\"'").lower() for token in text.split() if token.strip()]


def _is_action_task(text: str) -> bool:
    tokens = _tokenize(text)
    return any(token in ACTION_KEYWORDS for token in tokens)


def _contains_code_block(text: str) -> bool:
    return "```" in text


def _contains_redundant_request(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in REDUNDANT_REQUEST_PATTERNS)


def _load_conversation_records(path: Path) -> list[dict[str, Any]]:
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


def _extract_alignment_signals(task_dir: Path) -> dict[str, Any]:
    conversation_path = task_dir / "conversation.jsonl"
    battery_dispatch_path = task_dir / "artifacts" / "battery_dispatch.json"
    local_text = ""
    reference_text = ""
    local_model = None
    reference_model = None

    for record in _load_conversation_records(conversation_path):
        role = str(record.get("role", "")).strip()
        source = str(record.get("source", "")).strip()
        message_type = str(record.get("message_type", "")).strip()
        metadata = record.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        content = str(record.get("content", "")).strip()
        if not content:
            continue
        if not local_text and role == "assistant" and source == "cloud" and message_type == "local_reasoning":
            local_text = content
            local_model = record.get("model")
        if (
            not reference_text
            and role == "assistant"
            and source == "cloud"
            and (
                message_type == "reasoning"
                or metadata.get("hybrid")
            )
        ):
            reference_text = content
            reference_model = record.get("model")
        if not reference_text and role == "assistant" and source == "codex":
            reference_text = content
            reference_model = record.get("model")

    selected_expert_count = 0
    cascade_outputs: list[dict[str, Any]] = []
    if battery_dispatch_path.exists():
        try:
            battery_payload = _read_json(battery_dispatch_path)
        except json.JSONDecodeError:
            battery_payload = {}
        selected_expert_count = int(battery_payload.get("selected_expert_count", 0) or 0)
        raw_cascade_outputs = battery_payload.get("cascade_outputs", [])
        if isinstance(raw_cascade_outputs, list):
            cascade_outputs = [item for item in raw_cascade_outputs if isinstance(item, dict)]

    return {
        "local_text": local_text,
        "reference_text": reference_text,
        "local_model": local_model,
        "reference_model": reference_model,
        "selected_expert_count": selected_expert_count,
        "cascade_outputs": cascade_outputs,
    }


def _compute_reward_components(
    *,
    user_goal: str,
    completed: float,
    value_score: float,
    file_change_count: int,
    tool_call_count: int,
    local_text: str,
    reference_text: str,
    selected_expert_count: int,
) -> dict[str, float]:
    action_task = _is_action_task(user_goal)
    local_len = len(local_text)
    reference_len = len(reference_text)
    length_ratio = round(local_len / max(reference_len, 1), 4) if local_len and reference_len else 1.0
    code_overproduction = bool(local_text and _contains_code_block(local_text) and not _contains_code_block(reference_text))
    redundant_request = bool(local_text and _contains_redundant_request(local_text) and not _contains_redundant_request(reference_text))

    reward_env = round(
        (0.60 * completed)
        + (0.25 * min(value_score, 1.0))
        + (0.10 if file_change_count > 0 else 0.0)
        + (0.05 if tool_call_count > 0 else 0.0),
        4,
    )

    reward_align = 0.0
    if reference_text and local_text:
        if local_len <= max(reference_len * 1.2, reference_len + 40):
            reward_align += 0.18
        elif local_len <= max(reference_len * 1.5, reference_len + 80):
            reward_align += 0.08
        if action_task and not redundant_request:
            reward_align += 0.12
        if not code_overproduction:
            reward_align += 0.08
        if selected_expert_count > 0 and selected_expert_count <= 2:
            reward_align += 0.04
    reward_align = round(reward_align, 4)

    energy_penalty = 0.0
    if local_len and reference_len:
        if length_ratio > 1.5:
            energy_penalty += min(0.22, round((length_ratio - 1.5) * 0.16, 4))
        elif length_ratio > 1.2:
            energy_penalty += min(0.10, round((length_ratio - 1.2) * 0.08, 4))
    if code_overproduction:
        energy_penalty += 0.12
    if redundant_request:
        energy_penalty += 0.15
    if selected_expert_count >= 3:
        energy_penalty += 0.05
    energy_penalty = round(energy_penalty, 4)

    reward_short = round(max(0.0, 0.24 - energy_penalty), 4)
    reward_total = round(max(0.0, reward_env + reward_align + reward_short - energy_penalty), 4)

    return {
        "reward_env": reward_env,
        "reward_align": reward_align,
        "reward_short": reward_short,
        "energy_penalty": energy_penalty,
        "reward_total": reward_total,
        "response_char_len": float(local_len),
        "reference_char_len": float(reference_len),
        "length_ratio": float(length_ratio),
        "action_task": 1.0 if action_task else 0.0,
        "code_overproduction": 1.0 if code_overproduction else 0.0,
        "redundant_request": 1.0 if redundant_request else 0.0,
    }


def _build_reward_records(task_runs_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        outcome_json = task_dir / "outcome.json"
        tool_trace_json = task_dir / "tool_trace.json"
        if not task_json.exists() or not outcome_json.exists():
            continue

        task_payload = _read_json(task_json)
        outcome_payload = _read_json(outcome_json)
        tool_payload = _read_json(tool_trace_json) if tool_trace_json.exists() else {"tool_calls": []}
        tool_calls = tool_payload.get("tool_calls", [])
        completed = 1.0 if outcome_payload.get("result_status") == "completed" else 0.0
        value_score = float(outcome_payload.get("value_score", 0.0))
        file_change_count = int(task_payload.get("file_change_count", 0))
        tool_call_count = int(task_payload.get("tool_call_count", 0))
        user_goal = str(task_payload.get("user_goal", ""))
        signals = _extract_alignment_signals(task_dir)
        reward_components = _compute_reward_components(
            user_goal=user_goal,
            completed=completed,
            value_score=value_score,
            file_change_count=file_change_count,
            tool_call_count=tool_call_count,
            local_text=str(signals.get("local_text", "")),
            reference_text=str(signals.get("reference_text", "")),
            selected_expert_count=int(signals.get("selected_expert_count", 0)),
        )
        records.append(
            {
                "task_id": task_payload.get("task_id", task_dir.name),
                "input": user_goal,
                "target": {
                    "result_status": outcome_payload.get("result_status"),
                    "tool_calls": tool_calls,
                    "file_change_count": file_change_count,
                },
                "reward": reward_components["reward_total"],
                "metadata": {
                    "source": "real_execution_feedback",
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": value_score,
                    "completed": bool(completed),
                    "tool_call_count": tool_call_count,
                    "file_change_count": file_change_count,
                    "reward_env": reward_components["reward_env"],
                    "reward_align": reward_components["reward_align"],
                    "reward_short": reward_components["reward_short"],
                    "energy_penalty": reward_components["energy_penalty"],
                    "response_char_len": int(reward_components["response_char_len"]),
                    "reference_char_len": int(reward_components["reference_char_len"]),
                    "length_ratio": reward_components["length_ratio"],
                    "action_task": bool(reward_components["action_task"]),
                    "code_overproduction": bool(reward_components["code_overproduction"]),
                    "redundant_request": bool(reward_components["redundant_request"]),
                    "selected_expert_count": int(signals.get("selected_expert_count", 0)),
                    "local_model": signals.get("local_model"),
                    "reference_model": signals.get("reference_model"),
                },
            }
        )
        for tool_index, tool_call in enumerate(tool_calls):
            if not isinstance(tool_call, dict):
                continue
            tool_name = str(tool_call.get("tool") or tool_call.get("name") or "").strip()
            if not tool_name:
                continue
            tool_status = str(tool_call.get("status", "completed")).strip()
            output_summary = str(tool_call.get("output_summary", ""))
            output_len = len(output_summary)
            tool_energy_penalty = 0.08 if output_len > 420 else 0.0
            if _contains_code_block(output_summary):
                tool_energy_penalty += 0.05
            tool_reward = round(
                (0.5 if tool_status == "completed" else 0.0)
                + (0.25 * value_score)
                + (0.15 if output_summary.strip() else 0.0)
                + (0.10 if file_change_count > 0 else 0.0),
                4,
            )
            tool_reward = round(max(0.0, tool_reward - tool_energy_penalty), 4)
            records.append(
                {
                    "task_id": f"{task_payload.get('task_id', task_dir.name)}-tool-{tool_index}",
                    "input": f"User goal: {task_payload.get('user_goal', '')}\nTool: {tool_name}",
                    "target": {
                        "status": tool_status,
                        "output_summary": output_summary,
                        "arguments": tool_call.get("arguments", {}),
                    },
                    "reward": tool_reward,
                    "metadata": {
                        "source": "real_execution_feedback_tool",
                        "route_mode": task_payload.get("route_mode"),
                        "value_score": value_score,
                        "completed": tool_status == "completed",
                        "tool_name": tool_name,
                        "tool_call_count": tool_call_count,
                        "file_change_count": file_change_count,
                        "reward_env": tool_reward,
                        "energy_penalty": round(tool_energy_penalty, 4),
                        "response_char_len": output_len,
                    },
                }
            )
    return records


def _build_preference_records(task_runs_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_task_ids: set[str] = set()
    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        artifact_json = task_dir / "artifacts" / "hybrid_refinement.json"
        if not task_json.exists() or not artifact_json.exists():
            continue

        task_payload = _read_json(task_json)
        artifact_payload = _read_json(artifact_json)
        user_goal = str(task_payload.get("user_goal", "")).strip()
        local_draft = str(artifact_payload.get("local_draft", "")).strip()
        cloud_refinement = str(artifact_payload.get("cloud_refinement", "")).strip()
        if not user_goal or not local_draft or not cloud_refinement:
            continue

        prompt = "\n".join(
            [
                f"User goal: {user_goal}",
                "Select the better planning response for the task.",
            ]
        )
        records.append(
            {
                "task_id": f"{task_payload.get('task_id', task_dir.name)}-preference",
                "prompt": prompt,
                "chosen": cloud_refinement,
                "rejected": local_draft,
                "metadata": {
                    "source": "hybrid_refinement_preference",
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "local_model": artifact_payload.get("local_model"),
                    "cloud_model": artifact_payload.get("cloud_model"),
                    "local_length": artifact_payload.get("local_length"),
                    "cloud_length": artifact_payload.get("cloud_length"),
                    "similarity_score": artifact_payload.get("metadata", {}).get("similarity_score"),
                    "local_quality_score": artifact_payload.get("metadata", {}).get("local_quality_score"),
                },
            }
        )
        seen_task_ids.add(str(task_payload.get("task_id", task_dir.name)))

    for task_dir in sorted(task_runs_root.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        conversation_jsonl = task_dir / "conversation.jsonl"
        if not task_json.exists() or not conversation_jsonl.exists():
            continue
        task_payload = _read_json(task_json)
        task_id = str(task_payload.get("task_id", task_dir.name))
        if task_id in seen_task_ids:
            continue
        if str(task_payload.get("route_mode", "")).strip() != "hybrid":
            continue

        user_goal = str(task_payload.get("user_goal", "")).strip()
        if not user_goal:
            continue
        local_draft = ""
        cloud_refinement = ""
        local_model = None
        cloud_model = None
        for line in conversation_jsonl.read_text("utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(record.get("role", "")) != "assistant":
                continue
            if str(record.get("source", "")) != "cloud":
                continue
            metadata = record.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            if str(record.get("message_type", "")).strip() == "local_reasoning" and not local_draft:
                local_draft = str(record.get("content", "")).strip()
                local_model = record.get("model")
            elif str(record.get("message_type", "")).strip() == "reasoning" and metadata.get("hybrid") and not cloud_refinement:
                cloud_refinement = str(record.get("content", "")).strip()
                cloud_model = record.get("model")

        if not local_draft or not cloud_refinement:
            continue

        prompt = "\n".join(
            [
                f"User goal: {user_goal}",
                "Select the better planning response for the task.",
            ]
        )
        records.append(
            {
                "task_id": f"{task_id}-preference",
                "prompt": prompt,
                "chosen": cloud_refinement,
                "rejected": local_draft,
                "metadata": {
                    "source": "hybrid_refinement_preference_conversation",
                    "route_mode": task_payload.get("route_mode"),
                    "value_score": task_payload.get("value_score", 0.0),
                    "local_model": local_model,
                    "cloud_model": cloud_model,
                    "local_length": len(local_draft),
                    "cloud_length": len(cloud_refinement),
                },
            }
        )
        seen_task_ids.add(task_id)
    return records


def build_rlef_datasets(task_runs_root: Path, datasets_root: Path) -> list[Path]:
    """Build minimal RLEF/reward datasets from real task outcomes."""
    datasets_root.mkdir(parents=True, exist_ok=True)
    reward_path = datasets_root / "rlef_reward.jsonl"
    preference_path = datasets_root / "rlef_preference.jsonl"

    reward_records = _build_reward_records(task_runs_root)
    preference_records = _build_preference_records(task_runs_root)

    _jsonl_write(reward_path, reward_records)
    _jsonl_write(preference_path, preference_records)
    return [reward_path, preference_path]
