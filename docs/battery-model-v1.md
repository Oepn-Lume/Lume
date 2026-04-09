# Battery Model V1

## Definition

`Battery Model = Gemma4 31B + LoRA`

In the `Lume` system, the Battery Model is the local continuation layer that inherits capability from real cloud usage and keeps working when cloud access is unavailable, expensive, or unnecessary.

## Components

- `Base Model`: `gemma4:31b`, served locally through `Ollama`
- `Adapter Layer`: LoRA weights distilled from real Codex/cloud dialogue, bootstrap guidance, execution traces, patch events, and code outputs
- `Runtime Role`: low-latency inference, offline continuity, high-frequency task handling, and local-first fallback

## Why This Matters

The Battery Model is the concrete implementation of `Token as Asset`.

- Cloud models deliver the first-pass premium reasoning
- `Shadow Logging` records what the cloud returned
- dataset builders turn those records into training corpora
- LoRA training converts those corpora into reusable local capability
- `Gemma4 31B + LoRA` becomes the persistent local asset

## Current Project Mapping

- Model config: `configs/models.yaml`
- Current adapter candidate: `data/distilled/transformers-lora-v2-realcloud/adapter`
- Real cloud datasets:
  - `data/datasets/real_cloud_bootstrap_sft.jsonl`
  - `data/datasets/real_cloud_full_fidelity_sft.jsonl`
  - `data/datasets/real_cloud_dialogue_sft.jsonl`
  - `data/datasets/real_code_execution_sft.jsonl`

## Intended Routing

- `Cloud-First`: new, difficult, high-risk, or high-value tasks
- `Hybrid`: cloud reasoning plus local continuation or execution support
- `Battery Model`: offline, low-risk, repetitive, or low-latency tasks

## Current Status

The Battery Model definition is now fixed across the project:

- local base = `Gemma4 31B`
- local adaptation = `LoRA`
- economic logic = convert cloud token spend into local reusable capability

The next engineering step is to connect `Ollama gemma4:31b` into the runtime router so that local inference can be evaluated on real task flows rather than standalone prompt tests.
