# Battery Model V1

`Battery Model = Gemma4 31B + Sentinel-LoRA`

In `Lume`, the Battery Model is the local continuation layer that absorbs cloud-returned intelligence and keeps working when cloud access is slow, unavailable, or too expensive.

## Components

- `Base Model`: `gemma4:31b` served locally through `Ollama`
- `Adapter Layer`: `Sentinel-LoRA`, distilled from real cloud dialogues, bootstrap guidance, execution traces, code outputs, and patch events
- `Runtime Role`: low-latency inference, offline continuity, and repeat-task reuse
- `SOH`: state-of-health style evaluation against stronger cloud baselines

## Data Sources

- `real_cloud_dialogue_sft.jsonl`
- `real_cloud_bootstrap_sft.jsonl`
- `real_cloud_full_fidelity_sft.jsonl`
- `real_code_execution_sft.jsonl`

## Current Status

The Battery Model definition is fixed at the project level, but the runtime still needs deeper routing integration so that `gemma4:31b` can take over selected real tasks automatically.
