# Lume Sentinel 2026

`Lume` is a local-first prototype for turning high-value AI usage into reusable assets.

## Battery Model

The working project definition is:

`Battery Model = Gemma4 31B + LoRA`

That means:

- `Gemma4 31B` is the local base model served by `Ollama`
- `LoRA` adapters are distilled from real cloud-returned sessions, bootstrap guidance, execution traces, and code outputs
- the `Battery Model` is the local continuation layer for offline, low-latency, and high-frequency tasks

Cloud models still provide first-pass premium reasoning. `Shadow Logging`, dataset building, and LoRA training convert that paid capability into reusable local assets.

## Starfire Protocol

`Lume Starfire Protocol` is the release-and-distribution layer that turns repository changes into collaborative signal.

Current implementation scope:

- repository messaging for the `Battery Model` narrative
- a GitHub Actions workflow skeleton for contribution intake and validation
- a safe `X` marketing executor that defaults to `dry-run`
- local watchman reporting so launch operations stay observable and low-anxiety

The protocol is designed to keep execution grounded:

- if the workspace is not a Git repository, release actions stop before branch/push steps
- if X credentials are not configured, the marketing executor renders plans and reports without posting
- if contributed artifacts fail validation, the workflow fails closed

## Contact

- Release contact: `dspwatch@gmail.com`

## Layout

- `docs/`: whitepaper, implementation plan, architecture appendix
- `configs/`: model, routing, retention configs
- `data/`: logs, wiki memory, datasets, distilled adapters
- `scripts/`: import, build, train, evaluate, generate entrypoints
- `src/lume/`: core Python modules
- `examples/`: example outputs and sample payloads
- `tests/`: test drafts and smoke checks

## Core Pipeline

The current minimum working loop is:

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

Main steps:

1. Import or sync session logs
   - `python scripts/import_codex_sessions.py`
   - `python scripts/sync_codex_training_data.py --skip-train`
2. Build datasets
   - `python scripts/build_distill_dataset.py`
3. Train a local adapter
   - `python scripts/train_lora.py`
4. Generate or evaluate
   - `python scripts/generate_local_response.py --prompt "写一篇爱国散文诗"`
   - `python scripts/evaluate_local_model.py`

Recommended Battery Model stack:

- Base model: `gemma4:31b` via `Ollama`
- Adapter: `data/distilled/transformers-lora-v2-realcloud/adapter`
- Primary purpose: bootstrap guidance, full-fidelity runtime behavior, and execution-style continuation

## Shadow Logging

Available logging paths:

- Batch import from JSON or CLI arguments:
  - `python scripts/collect_shadow_logs.py`
- Runtime incremental recording:
  - `src/lume/logging/recorder.py`
  - `src/lume/execution/session.py`
  - `src/lume/execution/runtime.py`
- Codex desktop session import:
  - `python scripts/import_codex_sessions.py`
- Continuous Codex sync:
  - `python scripts/watch_codex_training_data.py --interval-seconds 30`

Structured task logs are written to `data/task_runs/<task_id>/`.

## Wiki Memory

Wiki memory is built from task logs:

- Build task pages:
  - `python scripts/build_wiki_entries.py`
- Output:
  - `data/wiki/index.md`
  - `data/wiki/log.md`
  - `data/wiki/tasks/*.md`

## Training

The default trainer is now a real `transformers + PEFT/LoRA` flow.

Recommended GPU command:

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\train_lora.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

Current Battery Model workflow:

1. Run `Gemma4 31B` locally through `Ollama`
2. Distill real Codex/cloud traces into LoRA adapters
3. Evaluate whether the adapter improves bootstrap and execution-style generations
4. Route suitable tasks to the local Battery Model

Useful options:

- `--training-mode transformers_peft_lora`
- `--model-name-or-path uer/gpt2-chinese-cluecorpussmall`
- `--model-name-or-path sshleifer/tiny-gpt2`
- `--max-samples 256`
- `--epochs 2`

Outputs are saved under `data/distilled/<run-name>/` and include:

- `adapter/`
- `tokenizer/`
- `training_config.json`
- `metrics.json`
- `sample_generation.txt`

Current best real-cloud LoRA checkpoint:

- `data/distilled/transformers-lora-v2-realcloud/`

This checkpoint is the current adapter candidate for the `Gemma4 31B` Battery Model path, even though the rapid-iteration trainer still uses a smaller transformer base during some experiments.

If a constrained environment cannot use `transformers/peft`, you can still force the old fallback:

```powershell
python scripts/train_lora.py --training-mode tiny_lm_fallback
```

## Synthetic Data Factory

Generate synthetic SFT samples:

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider mock
```

If a cloud key is available later:

```powershell
python scripts/generate_100k_dataset.py --task-count 1000 --provider openai
```

Synthetic outputs land in:

- `data/generated_corpus/generated_raw/`
- `data/generated_corpus/generated_scored/`
- `data/generated_corpus/generated_final/`

For a real-cloud-only campaign that must not fall back to mock data:

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\generate_real_cloud_dataset.py --target-count 1000 --batch-size 50
```

This campaign stops immediately if a real provider is unavailable and only writes records that are marked `real_cloud=true`.

## Continuous Training Refresh

Incremental Codex sync plus retraining:

```powershell
python scripts/sync_codex_training_data.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

Continuous watch mode:

```powershell
python scripts/watch_codex_training_data.py --interval-seconds 30
```
