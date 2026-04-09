# Lume Treasury: Your Private Intelligence Treasury

> **Cloud conversations, local savings. Stop consuming AI. Start owning it.**

For the Chinese version, see [README.zh-CN.md](./README.zh-CN.md).

`Lume Treasury` is a local-first AI systems prototype designed to convert high-value cloud usage into reusable local assets.

It is not only a tooling project. It is an operating model for:

- capturing real cloud-returned intelligence
- distilling it into local capability
- routing repeatable work into a local Battery Model
- reducing long-term dependence on rented intelligence

---

## Runtime Requirements

Before running `Lume Treasury`, make sure these two local components are installed:

- `Codex`: used as the local execution and coding runtime  
  Link: [https://openai.com/codex/](https://openai.com/codex/)
- `Ollama`: used to serve the local Battery Model such as `gemma4:31b`  
  Link: [https://ollama.com/](https://ollama.com/)

Recommended environment:

- Windows with PowerShell
- NVIDIA GPU such as `RTX 5090` for local training
- Python environment with `torch`, `transformers`, and `peft`

---

## Core Thesis: Token as an Asset

In the default API economy, Tokens are consumed and disappear.

In `Lume Treasury`, Tokens are treated as capital expenditure for local intelligence.

- `Shadow Mode`: capture real cloud-returned dialogue, bootstrap guidance, execution traces, patch events, and tool outputs
- `Intelligence Backflow`: distill paid cloud capability into local datasets, memory structures, and LoRA adapters
- `Execution Feedback`: use real task outcomes as signals for what should be reinforced, retained, or rejected
- `Asset Reuse`: route recurring work to the local model once patterns have been absorbed

The goal is simple: every expensive cloud interaction should leave behind a persistent local advantage.

---

## Battery Model

`Battery Model = Gemma4 31B + Sentinel-LoRA`

The Battery Model is Lume's offline survival core and low-latency continuation layer.

- `Base`: `Gemma4 31B` served locally through `Ollama`
- `Adapter`: `Sentinel-LoRA`, distilled from real cloud sessions, bootstrap guidance, execution traces, and code outputs
- `Role`: continue useful work when cloud access is unavailable, too expensive, or unnecessary
- `SOH (State of Health)`: evaluate local alignment against stronger cloud baselines through repeated discharge-style testing

This is the practical meaning of digital sovereignty inside `Lume Treasury`: the local node keeps getting stronger as more paid intelligence is converted into local capability.

---

## Featured Essay

### Intellectual Sovereignty: How Lume Turns Every AI Chat into a Permanent Asset

We are living through a form of compute colonization. You pay to ask questions, the cloud model gets smarter, and you are left with a bill and no lasting ownership. `Lume Treasury` takes the opposite position: every high-value cloud interaction should become an investment in your own local intelligence.

Imagine every deep conversation with a frontier model being silently copied, structured, and distilled into a compact shadow brain on your own machine. That local brain remembers your coding patterns, your reasoning preferences, and your operating style. It becomes useful again on the next task instead of vanishing with the session.

#### The Alchemy: From Consumable Token to Permanent Asset

In the default API economy, Tokens are fuel. In `Lume Treasury`, Tokens are capital expenditure. This is the logic of Token Assetization.

- `Silent Capture`: `Shadow Logging` records not only final answers, but planning steps, decision forks, corrections, and tool outputs
- `Asymmetric Distillation`: `Sentinel-LoRA` extracts compact task logic from cloud traces without trying to clone the entire cloud model
- `Battery Model`: `Gemma4 31B + Sentinel-LoRA` creates a local continuation layer that can take over when cloud use is unavailable, too expensive, or unnecessary

#### State of Health

Lume treats local-model honesty as an engineering problem. `SOH (State of Health)` runs repeated discharge-style evaluations against stronger baselines, while real execution feedback asks grounded questions: Did the code run? Did the output hold up? Did the task actually succeed?

This keeps the local model tied to reality instead of drifting into decorative intelligence.

#### Conclusion

`Lume Treasury` is not just a toolchain. It is a stance on digital sovereignty.

By turning rented cloud intelligence into locally retained capability, `Lume Treasury` helps move the user from tenant to owner. The next cloud conversation is not only a cost. It is a building block.

**Project Info**

- Organization: `Oepn-Lume`
- GitHub: [https://github.com/Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- Core Tenets: `Local-first AI`, `Token Assetization`, `Digital Sovereignty`
- Email: `dspwatch@gmail.com`
- Source inspiration: [X post by @wuyifree](https://x.com/wuyifree/status/2042179788329341352)

---

## Quick Start

### 1. Import real Codex/cloud traces

```powershell
python scripts/import_codex_sessions.py
```

### 2. Build distillation datasets

```powershell
python scripts/build_distill_dataset.py
```

### 3. Train the local adapter

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\train_lora.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

---

## Project Layout

- `configs/`: model, routing, and retention configuration
- `data/`: raw logs, generated corpora, datasets, marketing outputs, and distilled checkpoints
- `docs/`: whitepaper, implementation plan, and Battery Model documents
- `scripts/`: dataset building, training, evaluation, sync, release, and marketing entrypoints
- `src/lume/logging/`: shadow logging and Codex session import
- `src/lume/distill/`: dialogue, execution, and historical code distillation
- `src/lume/execution/`: runtime wrappers and cloud/local execution bridges
- `src/lume/memory/`: Wiki memory builders
- `src/lume/routing/`: routing rules between cloud and local paths

---

## Working Pipeline

The current minimum working loop is:

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

Current production-oriented stack:

- local base model: `gemma4:31b`
- local provider: `Ollama`
- current LoRA candidate: `data/distilled/transformers-lora-v2-realcloud/adapter`
- real-cloud corpus layers:
  - `real_cloud_dialogue_sft.jsonl`
  - `real_cloud_bootstrap_sft.jsonl`
  - `real_cloud_full_fidelity_sft.jsonl`
  - `real_code_execution_sft.jsonl`

---

## Project Progress

This section is the running changelog for implemented milestones. New shipped features should be added here as they land.

- [x] `Shadow Logging`: real Codex/session traces, cloud-visible messages, tool calls, and task artifacts are captured locally
- [x] `LLM Wiki Memory`: task runs can be distilled into structured wiki pages and update logs
- [x] `Dataset Builder`: dialogue, execution, memory, hybrid-refinement, historical-code, and real-cloud datasets are generated from logs
- [x] `Battery Routing`: the router can choose `cloud`, `local`, or `hybrid` using similarity, complexity, and local quality snapshots
- [x] `Battery Model Runtime`: `Gemma4 31B` via `Ollama` is wired into the execution path as the local planning layer
- [x] `LoRA Training`: `transformers + PEFT/LoRA` training runs on local datasets with RTX 5090 support
- [x] `Evaluation Reports`: local-model evaluation, quality snapshots, and quality history are persisted to disk
- [x] `Hybrid Refinement Logging`: local drafts and cloud refinements are stored as structured comparison artifacts
- [x] `RLEF Dataset Layer`: real execution outcomes and hybrid preferences are converted into `rlef_reward.jsonl` and `rlef_preference.jsonl`
- [x] `Minimal Preference Optimization`: a first `DPO`-style LoRA training path is implemented for preference data
- [ ] `RLEF Scale-Up`: increase preference pairs and execution feedback coverage for stronger reinforcement signals
- [ ] `Reward-Aware Routing`: feed preference win-rate and execution rewards back into routing decisions
- [ ] `Continuous Retraining`: automate periodic `build -> train -> evaluate -> route-update` cycles

---

## Developer Commitments

- `Privacy First`: raw user data should stay local by default
- `Execution over Theater`: claims should be backed by traces, datasets, tests, and checkpoints
- `Hardware Equity`: optimize for practical local hardware paths, including `RTX` and `Apple Silicon`
- `Low-Anxiety Operations`: provide watchman reports, not information floods

---

## Contact

- Release contact: `dspwatch@gmail.com`
- Organization: [Oepn-Lume](https://github.com/Oepn-Lume)
