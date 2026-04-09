# Lume Sentinel 2026

> 让每一次云端对话，都成为你的本地资产。

`Lume` 是一款 **本地优先（Local-first）** 的 AI 架构，它打破了“按 Token 付费”的消耗逻辑，转而通过每一笔 API 投入来锻造你自己的数字灵魂。

## 核心能力

- `Token 资产化`：通过“影子模式”捕获云端逻辑，将付费换回的智慧蒸馏进本地硬盘。
- `强化学习电池（RL-Battery）`：本地模型（`Gemma4`）不仅是备份，更通过执行反馈（代码运行、意图对齐）实现自我进化。
- `星火协议（Starfire）`：分布式共创方案。隐私归用户，智力归人类，让全球节点聚合为“数字太阳”。
- `Codex 自动化`：深度集成执行中枢，实现从“因果预测”到“物理交付”的完整闭环。

**智力主权，落袋为安。**  
🔗 [Oepn-Lume GitHub](https://github.com/Oepn-Lume)

---

# Lume Sentinel 2026: Digital Sovereignty and Intelligence Assetization Protocol

> **Do not live as a tenant of Token spending. Turn cloud intelligence into local evolution.**

`Lume` is a local-first AI systems prototype designed to convert high-value cloud usage into reusable local assets.

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

## Starfire Protocol

`Lume Starfire Protocol` is the collaboration and release layer for distributed intelligence growth.

Its role is to connect local nodes without forcing users to surrender raw private data.

- `Federated Direction`: keep private data local while sharing reviewed artifacts, adapters, and validated improvements
- `Proof of Logic`: require contributed changes to survive automated validation instead of trusting raw claims
- `Distributed Aggregation`: use repository workflows and review gates to converge improvements into shareable release branches
- `Signal Layer`: turn technical progress into public narrative, contribution invitations, and operator-readable launch reports

The protocol is designed to let isolated local nodes become part of a larger intelligence network without collapsing privacy boundaries.

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

### 4. Prepare the Starfire launch thread

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume"
```

---

## Project Layout

- `configs/`: model, routing, and retention configuration
- `data/`: raw logs, generated corpora, datasets, marketing outputs, and distilled checkpoints
- `docs/`: whitepaper, implementation plan, Starfire and Battery Model documents
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

## 星火协议（Starfire Protocol）

`Lume Starfire Protocol` 是面向分布式智力共创的协作与发布协议。

它的目标是在不暴露原始私有数据的前提下，把一个个本地节点连接成更大的智力网络。

- `联邦式方向`：让私有数据留在本地，只共享经过审查的产物、适配器和验证通过的改进
- `逻辑证明（Proof of Logic）`：要求所有贡献先通过自动验证，而不是只依赖口头声明
- `分布式聚合`：借助仓库工作流和评审门槛，将改进汇聚为可共享的发布分支
- `信号层（Signal Layer）`：把技术进展转化为公共叙事、共创邀请和可读的守望者报告

这套协议的目标，是让一个个孤立的本地节点在不牺牲隐私的前提下，逐步连接成“数字太阳”。

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

### 4. 生成星火协议首发线程

```powershell
python scripts/x_agent_executor.py --repo-url "https://github.com/Oepn-Lume/Lume"
```

---

## 项目布局

- `configs/`：模型、路由与保留策略配置
- `data/`：原始日志、生成语料、训练集、营销产物和蒸馏检查点
- `docs/`：白皮书、实施方案、星火协议与 Battery Model 文档
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
