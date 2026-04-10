# 🪙 Lume Treasury: Your Private Intelligence Vault

> **"Cloud conversations, local savings. Stop consuming AI. Start owning it."**

**Lume Treasury** is a local-first AI system that reclaims the value of cloud AI usage. In the current token economy, intelligence is rented and ephemeral. Lume changes the paradigm: **every interaction with a frontier model is treated as a capital investment in your own local brain.**

---

## Runtime Requirements

Before running `Lume Treasury`, make sure these two local components are installed:

- **Codex**: used as the local execution and coding runtime  
  Link: [https://openai.com/codex/](https://openai.com/codex/)
- **Ollama**: used to serve the local Battery Model such as `gemma4:31b`  
  Link: [https://ollama.com/](https://ollama.com/)

---

## 🚀 Quick Start

```bash
# Clone and enter the repo
git clone https://github.com/Oepn-Lume/Lume.git
cd Lume

# One command to start shadow mode and begin capturing cloud-returned intelligence
python main.py
```

Other entry modes:

```bash
# Sync Codex sessions into datasets and optionally retrain
python main.py sync

# Run the full continuous retraining loop
python main.py cycle

# Run the end-to-end demo pipeline for a task
python main.py pipeline --task "write a short summary"
```

---

## 🛠 Hardware Matrix

| Hardware Platform | Recommended Model | Run Mode |
| :--- | :--- | :--- |
| **NVIDIA RTX 5090** | Gemma4 31B (Full) | 4-bit / 8-bit local training |
| **Mac Pro (M2/M3 Ultra)** | Gemma4 31B | Metal acceleration / Ollama |
| **RTX 3060 / 4070** | Gemma4 9B | LoRA inference |

---

## Wiki

The project wiki is now versioned inside the repository so analysis, memory pages, and long-form notes are directly viewable on GitHub.

- **Wiki Index**: [wiki/index.md](./wiki/index.md)
- **Gemma4 Analysis**: [wiki/analysis/gemma-vs-cloud-overview.md](./wiki/analysis/gemma-vs-cloud-overview.md)

---

## Blog Posts

- **Why Gemma4 Still Cannot Replace Cloud Collaboration**: [docs/en/blogs/gemma4-vs-cloud-full-history.md](./docs/en/blogs/gemma4-vs-cloud-full-history.md)
- **Before the Digital Blackout: Why We Need a Digital Sun Plan**: [docs/en/blogs/digital-sun-before-the-blackout.md](./docs/en/blogs/digital-sun-before-the-blackout.md)
- **Built for the Worksite: From "Library Researcher" to "Always-On Teammate"**: [docs/en/blogs/built-for-the-worksite.md](./docs/en/blogs/built-for-the-worksite.md)
- **Gemma4 Analysis in Wiki**: [wiki/analysis/gemma-vs-cloud-overview.md](./wiki/analysis/gemma-vs-cloud-overview.md)

---

## 💎 The Core Thesis: Token as an Asset

In the default API economy, tokens are fuel: burned and forgotten. In **Lume**, tokens are **Capital Expenditure (CapEx)** for private intelligence.

- **Shadow Mode**: Silently captures cloud reasoning, tool outputs, and execution traces.
- **Intelligence Backflow**: Distills expensive cloud logic into private LoRA adapters.
- **Execution Feedback**: Uses real-world task success signals such as “Did the code run?” to reinforce local performance.
- **Asset Reuse**: Once a pattern is absorbed, the local model takes over, saving money and latency.

---

## 🔋 The Battery Model (Gemma4 + Sentinel-LoRA)

The **Battery Model** is Lume’s offline survival core. It is not just a model; it is a **growing asset**.

- **Base**: `Gemma4 31B` served via `Ollama`
- **Adapter**: `Sentinel-LoRA`, distilled from specific cloud sessions and coding patterns
- **SOH (State of Health)**: A metric that evaluates how healthy and aligned the local model is compared with stronger cloud baselines
- **The Goal**: The local node gets stronger every time the cloud is used. **Digital sovereignty starts here.**

---

## 🧠 Why Lume? (The Alchemy of Ownership)

We are living through **compute colonization**. People pay to improve somebody else’s model and keep the bill. Lume flips the script:

1. **Silent Capture**: Records planning steps, decision forks, corrections, and the hidden logic of AI work.
2. **Asymmetric Distillation**: Lume does not try to clone the cloud. It extracts the **logic** that is actually useful.
3. **Local Awakening**: The computer stops being a dumb terminal and starts becoming an expert partner.

---

## 🚀 Working Pipeline: The Loop of Evolution

Lume operates on a continuous improvement cycle:

1. **Capture**: Log real Codex and cloud traces.
2. **Synthesize**: Build high-fidelity distillation datasets (`jsonl`).
3. **Train**: Run local LoRA training.
4. **Route**: Let the system decide whether the local Battery Model can handle the task now.

---

## 🛠 Project Progress & Milestones

| Feature | Description | Status |
| :--- | :--- | :--- |
| **Shadow Logging** | Capture tool calls, task artifacts, and cloud-visible reasoning traces. | ✅ |
| **LLM Wiki Memory** | Distill task runs into reusable structured memory pages. | ✅ |
| **One-Command Launcher** | Start shadow logging or common workflows through `python main.py`. | ✅ |
| **Battery Routing** | Hybrid cloud/local execution based on complexity and local quality. | ✅ |
| **Expert Battery Matrix** | Smart-gated local experts for general, code, creative, and privacy tasks. | ✅ |
| **Dynamic Expert Cascades** | Select 1-3 local experts per task and record cascade outputs for later training. | ✅ |
| **Battery Cascade Dataset** | Convert expert-to-expert refinement chains into trainable supervision records. | ✅ |
| **On-site Alignment Dataset** | Turn full session comparisons into stateful cloud-vs-local supervision and DPO pairs. | ✅ |
| **Dynamic Snapshot Injector** | Inject `<field_report>` context and short-command expansion before local planning. | ✅ |
| **On-site DPO Augmentation** | Expand full-history cloud-vs-local comparisons into 3000+ preference pairs for state-aware DPO tuning. | ✅ |
| **Digital Sun Share Manifest** | Local expert-weight share manifests for future federated synchronization. | ✅ |
| **Battery Model Runtime** | Run `gemma4:31b` through `Ollama` as the local planning layer. | ✅ |
| **LoRA Training** | PEFT training on local hardware. | ✅ |
| **Evaluation Reports** | Persist local quality snapshots, reports, and historical evaluation records. | ✅ |
| **Hybrid Refinement Logging** | Record local drafts versus cloud refinements as structured artifacts. | ✅ |
| **Execution Dataset Expansion** | Extract real code files, function-call outputs, hybrid artifacts, and tool-level feedback into trainable datasets. | ✅ |
| **RLEF Layer** | Reinforcement Learning from Execution Feedback datasets and minimal preference optimization. | 🏗️ In Progress |
| **Energy-Aware RLEF** | Add action alignment, verbosity penalties, and expert-cost penalties to reward shaping for on-device learning. | ✅ |
| **Continuous Retraining** | Run `Build -> Train -> Evaluate -> Route` through `python main.py cycle`. | ✅ |

---

## 🤝 Developer Commitments

- **Privacy First**: Raw user data should stay local by default.
- **Execution over Theater**: Claims should be backed by traces, datasets, tests, and checkpoints.
- **Hardware Equity**: Optimize for the hardware people actually own.
- **Low-Anxiety Ops**: Provide watchman reports, not information floods.

---

## 📬 Get in Touch

- **GitHub**: [Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- **Email**: `dspwatch@gmail.com`
- **Inspiration**: Built around the Token Assetization thesis.
