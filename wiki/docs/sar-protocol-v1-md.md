---
id: sar-protocol-v1-md
type: doc
relative_path: sar-protocol-v1.md
language: mixed
section: root
---

# SAR Protocol V1

## Source
- Path: `sar-protocol-v1.md`
- Language: `mixed`
- Section: `root`
- Original file: [sar-protocol-v1.md](C:/Users/yh-PC-003/Desktop/codex/lume/docs/sar-protocol-v1.md)

## Body

# SAR Protocol V1

## Overview

`SAR` means `State-Action-Reward`.

In `Lume Treasury`, `SAR` is the standardized interface for turning task execution into a reusable Battery Model training signal. The protocol is designed so future agents do not need to understand the full `Lume` software-agent stack in order to participate. They only need to provide:

- a structured **state**
- a structured **action**
- a structured **reward**

This makes the Battery Model evolvable beyond code-only workflows and prepares the project for future robotics, mobile, IoT, and other edge-agent domains.

Current protocol version:

- `sar-v1`

## Design Goals

The protocol is designed around four goals.

First, it must be small enough to generate from real task traces without adding large runtime overhead.

Second, it must be explicit enough to let different domains map into the same training surface.

Third, it must preserve engineering feedback, because `Lume` optimizes for real-world action quality rather than language style alone.

Fourth, it must be stable enough to serve as a contract between the Battery runtime, dataset builders, and future external agents.

Fifth, it must be adapter-driven, so new domains can be integrated without rewriting the core SAR dataset builder.

## Record Structure

Each record is a single JSON object with the following top-level keys:

- `protocol_version`
- `record_id`
- `agent_type`
- `state`
- `action`
- `reward`
- `metadata`

Example:

```json
{
  "protocol_version": "sar-v1",
  "record_id": "demo-task-sar",
  "agent_type": "software-agent",
  "state": {
    "domain": "software",
    "world_snapshot": {
      "task_id": "demo-task",
      "route_mode": "hybrid"
    },
    "intent_trajectory": [
      {
        "user_goal": "debug code"
      }
    ],
    "feedback_signals": {
      "result_status": "completed"
    },
    "metadata": {}
  },
  "action": {
    "action_type": "function_call",
    "action_payload": {
      "tool_name": "battery_matrix_dispatch",
      "summary": "Selected local experts"
    },
    "confidence": 0.8,
    "executor": "codex",
    "metadata": {}
  },
  "reward": {
    "total_reward": 0.91,
    "reward_align": 0.95,
    "reward_env": 1.0,
    "reward_short": 0.9,
    "energy_penalty": 0.03,
    "success": true,
    "metadata": {
      "tool_call_count": 1
    }
  },
  "metadata": {
    "source": "shadow_task_run"
  }
}
```

## Field Definitions

### `protocol_version`

The current protocol identifier.

Allowed value:

- `sar-v1`

Any producer or consumer that sees a different version should treat it as a compatibility boundary.

### `record_id`

A unique stable identifier for the SAR record.

Recommended form:

- `<task_id>-sar`

### `agent_type`

The coarse agent class that produced the trace.

Current allowed values:

- `software-agent`
- `robot-agent`
- `drone-agent`
- `voice-agent`
- `iot-agent`
- `generic-agent`

### `state`

The structured view of the environment at decision time.

Required fields:

- `domain`
- `world_snapshot`
- `intent_trajectory`
- `feedback_signals`

Optional field:

- `metadata`

Current allowed `domain` values:

- `software`
- `robotics`
- `drone`
- `voice`
- `iot`
- `generic`

`world_snapshot` should contain the current environment state. In software tasks this may include route mode, model used, changed files, or output source. In robotics it may later include pose, sensor summaries, or motion buffers.

`intent_trajectory` should capture the immediate decision path that led to the action. This is intentionally a sequence so different agents can expose short-horizon state transitions without forcing a single fixed schema.

`feedback_signals` should contain observable, domain-level outcomes such as status, counts, success markers, or sensor-derived evaluation signals.

### `action`

The standardized action selected by the agent.

Required fields:

- `action_type`
- `action_payload`

Optional fields:

- `confidence`
- `executor`
- `metadata`

Current allowed `action_type` values:

- `deliver_result`
- `function_call`
- `patch_apply`
- `shell_command`
- `route_decision`
- `sensor_command`
- `motion_command`
- `state_update`

This layer is intentionally abstract. The goal is not to reproduce raw natural language, but to capture the meaningful action surface that the Battery Model should learn to bias toward.

### `reward`

The protocol reward object expresses how well the chosen action performed.

Required field:

- `total_reward`

Current standard subfields:

- `reward_align`
- `reward_env`
- `reward_short`
- `energy_penalty`
- `success`
- `metadata`

These fields are aligned with `Lume`'s current engineering-first training philosophy:

- `reward_align`: how well the action matched the validated path
- `reward_env`: whether the action succeeded in the real environment
- `reward_short`: whether the action was concise and energy-friendly
- `energy_penalty`: cost pressure that discourages wasteful inference or action chains

## Current Reference Mapping in Lume

Today, `Lume` exports SAR from `task_runs`.

The export path is now adapter-based. The core dataset builder resolves a domain adapter first, then asks that adapter to construct the `SARRecord`. This means future domains can plug into the same export path by implementing the adapter contract rather than patching the main builder.

The current reference mapping is:

- task metadata -> `state.world_snapshot`
- routing reasons and planning strategy -> `state.intent_trajectory`
- result status and counts -> `state.feedback_signals`
- first tool call -> `action`
- execution-derived reward shaping -> `reward`

This is intentionally conservative. `sar-v1` should be viewed as a stable minimum contract, not the final ceiling.

## Adapter Contract

`Lume` now treats SAR conversion as an adapter problem.

Each adapter must answer two questions:

- does this adapter support the current task source?
- if so, how should that source be mapped into a `SARRecord`?

The current default adapter is:

- `SoftwareTaskRunAdapter`

It maps existing `task_runs` into `software-agent` records.

The adapter registry exists so future domains can be added cleanly, for example:

- robotics task logs
- drone flight traces
- IoT control events
- voice-agent interaction sessions

This keeps the protocol stable while letting domain-specific extraction logic evolve independently.

## Validation Rules

The current protocol implementation enforces these constraints:

- top-level protocol version must equal `sar-v1`
- `domain` must be one of the known domain enums
- `agent_type` must be one of the known agent enums
- `action_type` must be one of the known action enums
- `world_snapshot`, `feedback_signals`, `action_payload`, and `metadata` must be mappings
- `intent_trajectory` must be a list
- `confidence`, when present, must be within `0.0` to `1.0`

These validations live in:

- `src/lume/spi/protocol.py`

## Evolution Policy

Future protocol evolution should follow these rules.

Backward-compatible additions such as new optional fields or new action/domain enums should increment the document but keep the runtime version unless old consumers would misread the meaning.

Any breaking change to required fields, semantics, or top-level structure should create a new protocol version such as `sar-v2`.

Battery runtime code should never silently reinterpret one version as another.

## Related Files

- `src/lume/spi/protocol.py`
- `src/lume/spi/adapters.py`
- `src/lume/spi/sar_dataset.py`
- `scripts/build_sar_dataset.py`
- `data/datasets/sar_protocol.jsonl`

