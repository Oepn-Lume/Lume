# Lume Treasury: Your Private Intelligence Treasury

> **Cloud conversations, local savings. Stop consuming AI. Start owning it.**

`Lume Treasury` is a local-first AI systems prototype designed to convert high-value cloud usage into reusable local assets.

It is not only a tooling project. It is an operating model for:

- capturing real cloud-returned intelligence
- distilling it into local capability
- routing repeatable work into a local Battery Model
- reducing long-term dependence on rented intelligence

---

## Core Thesis: Token as an Asset

In the default API economy, Tokens are consumed and disappear.

In `Lume`, Tokens are treated as capital expenditure for local intelligence.

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

This is the practical meaning of digital sovereignty inside `Lume`: the local node keeps getting stronger as more paid intelligence is converted into local capability.

---

## Featured Essay

### Intellectual Sovereignty: How Lume Turns Every AI Chat into a Permanent Asset

We are living through a form of compute colonization. You pay to ask questions, the cloud model gets smarter, and you are left with a bill and no lasting ownership. `Lume` takes the opposite position: every high-value cloud interaction should become an investment in your own local intelligence.

Imagine every deep conversation with a frontier model being silently copied, structured, and distilled into a compact shadow brain on your own machine. That local brain remembers your coding patterns, your reasoning preferences, and your operating style. It becomes useful again on the next task instead of vanishing with the session.

#### The Alchemy: From Consumable Token to Permanent Asset

In the default API economy, Tokens are fuel. In `Lume`, Tokens are capital expenditure. This is the logic of Token Assetization.

- `Silent Capture`: `Shadow Logging` records not only final answers, but planning steps, decision forks, corrections, and tool outputs
- `Asymmetric Distillation`: `Sentinel-LoRA` extracts compact task logic from cloud traces without trying to clone the entire cloud model
- `Battery Model`: `Gemma4 31B + Sentinel-LoRA` creates a local continuation layer that can take over when cloud use is unavailable, too expensive, or unnecessary

#### State of Health

Lume treats local-model honesty as an engineering problem. `SOH (State of Health)` runs repeated discharge-style evaluations against stronger baselines, while real execution feedback asks grounded questions: Did the code run? Did the output hold up? Did the task actually succeed?

This keeps the local model tied to reality instead of drifting into decorative intelligence.

#### Conclusion

`Lume V5.0` is not just a toolchain. It is a stance on digital sovereignty.

By turning rented cloud intelligence into locally retained capability, `Lume` helps move the user from tenant to owner. The next cloud conversation is not only a cost. It is a building block.

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

---

# Lume Sentinel 2026：数字主权与智力资产化协议

> **不要做 Token 的佃农，在本地开启你的强化学习式进化。**

`Lume` 是一个本地优先（Local-first）的 AI 系统原型，目标是把高价值的云端智能消耗转化为可复用、可沉淀、可继承的本地资产。

它不只是一个工具项目，而是一套围绕以下目标展开的运行体系：

- 捕捉真实云端返回的智力内容
- 将这些能力蒸馏到本地模型与记忆层
- 把可重复任务逐步路由到本地 Battery Model
- 降低对租赁型智能的长期依赖

---

## 核心思想：Token 资产化

在传统 API 模式下，Token 是一次性燃料，用完即失。

在 `Lume` 体系中，Token 被视为对本地智力资产的投资。

- `影子模式（Shadow Mode）`：捕捉真实云端返回的对话、启动指导、执行轨迹、补丁事件和工具输出
- `智力回流（Intelligence Backflow）`：把这些付费能力转化为本地数据集、记忆结构和 LoRA 适配器
- `执行反馈（Execution Feedback）`：根据真实任务结果判断哪些模式值得强化、保留或剔除
- `资产重用（Asset Reuse）`：当模式被本地吸收后，将重复工作路由给本地模型执行

这套系统的核心目标很直接：每一次昂贵的云端调用，都应该留下可持续的本地收益。

---

## 电池模型（Battery Model）

`Battery Model = Gemma4 31B + Sentinel-LoRA`

电池模型是 `Lume` 的离线生存核心，也是低延迟续航层。

- `基座`：通过 `Ollama` 在本地运行的 `Gemma4 31B`
- `适配器`：`Sentinel-LoRA`，由真实云端会话、启动指导、执行轨迹与代码产物蒸馏得到
- `角色`：在云端不可达、成本过高或没有必要调用云端时，继续承接高频任务
- `SOH（State of Health）`：通过持续的放电测试评估本地模型和强云端基线之间的对齐程度

这就是 `Lume` 中“数字主权”的工程化含义：你用过的云端智能，会不断沉淀为本地节点的长期能力。

---

## 快速开始

### 1. 导入真实 Codex / 云端轨迹

```powershell
python scripts/import_codex_sessions.py
```

### 2. 构建蒸馏数据集

```powershell
python scripts/build_distill_dataset.py
```

### 3. 训练本地适配器

```powershell
C:\Users\yh-PC-003\Desktop\codex\wan22\venv\Scripts\python.exe scripts\train_lora.py --device cuda --model-name-or-path uer/gpt2-chinese-cluecorpussmall
```

## 项目布局

- `configs/`：模型、路由与保留策略配置
- `data/`：原始日志、生成语料、训练集、营销产物和蒸馏检查点
- `docs/`：白皮书、实施方案与 Battery Model 文档
- `scripts/`：数据构建、训练、评估、同步、发布与营销脚本入口
- `src/lume/logging/`：影子日志与 Codex 会话导入
- `src/lume/distill/`：对话、执行与历史代码蒸馏模块
- `src/lume/execution/`：运行时包装器和云端/本地执行桥接层
- `src/lume/memory/`：Wiki 记忆构建器
- `src/lume/routing/`：云端与本地路径之间的路由规则

---

## 当前工作流水线

当前最小可运行闭环是：

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

当前面向生产的推荐栈是：

- 本地基座模型：`gemma4:31b`
- 本地提供方：`Ollama`
- 当前 LoRA 候选：`data/distilled/transformers-lora-v2-realcloud/adapter`
- 真实云端语料层：
  - `real_cloud_dialogue_sft.jsonl`
  - `real_cloud_bootstrap_sft.jsonl`
  - `real_cloud_full_fidelity_sft.jsonl`
  - `real_code_execution_sft.jsonl`

---

## 开发者承诺

- `隐私优先`：原始用户数据默认留在本地
- `执行优先于表演`：所有能力都应由日志、数据集、测试和检查点支撑
- `硬件平权`：面向 `RTX` 和 `Apple Silicon` 等现实本地硬件路径优化
- `减少焦虑`：提供守望者报告，而不是制造信息洪流

---

## 联系方式

- 发布联系邮箱：`dspwatch@gmail.com`
- 组织主页：[Oepn-Lume](https://github.com/Oepn-Lume)
---

## 项目进度

这一节用于维护已经落地的功能进展。后续每实现一个新能力，都应继续追加到这里。

- [x] `Shadow Logging`：已经能记录真实 Codex 会话、云端可见消息、工具调用和任务产物
- [x] `LLM Wiki Memory`：已经能把任务运行结果沉淀成结构化 wiki 页面和更新日志
- [x] `Dataset Builder`：已经能从日志生成对话、执行、记忆、hybrid 对比、历史代码和真实云端数据集
- [x] `Battery Routing`：路由器已经能基于相似度、复杂度和本地质量快照在 `cloud / local / hybrid` 之间切换
- [x] `Battery Model Runtime`：`Gemma4 31B` 已通过 `Ollama` 接入运行时，作为本地规划层参与执行
- [x] `LoRA Training`：已经支持 `transformers + PEFT/LoRA` 本地训练，并可调用 `RTX 5090`
- [x] `Evaluation Reports`：已经支持本地模型评估报告、质量快照和质量历史记录
- [x] `Hybrid Refinement Logging`：已经能把本地草稿和云端精修结果结构化保存
- [x] `RLEF Dataset Layer`：已经能把真实执行结果和 hybrid 偏好转换成 `rlef_reward.jsonl` 与 `rlef_preference.jsonl`
- [x] `Minimal Preference Optimization`：已经实现第一版基于偏好数据的 `DPO` 风格 LoRA 训练路径
- [ ] `RLEF Scale-Up`：继续扩大偏好样本和执行反馈覆盖面，增强强化学习信号
- [ ] `Reward-Aware Routing`：把偏好胜率和真实执行奖励反向接入路由决策
- [ ] `Continuous Retraining`：自动化周期性 `build -> train -> evaluate -> route-update` 闭环
