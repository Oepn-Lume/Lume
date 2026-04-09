# Lume Treasury：你的私人智力金库

> **云端对话，本地储蓄。别再消费 AI，去拥有它。**

如需英文版，请查看 [README.md](./README.md)。

`Lume Treasury` 是一个本地优先（Local-first）的 AI 系统原型，目标是把高价值云端调用转化为可复用、可积累、可继承的本地智能资产。

它不只是一个工具项目，更是一套围绕以下目标展开的运行体系：

- 捕捉真实云端返回的智能内容
- 将这些能力蒸馏到本地模型与记忆层
- 把可重复任务逐步路由到本地 Battery Model
- 降低对“租赁式智能”的长期依赖

---

## 运行条件

运行 `Lume Treasury` 前，需要在本地安装以下两个组件：

- `Codex`：作为本地执行与编码运行时  
  链接：[https://openai.com/codex/](https://openai.com/codex/)
- `Ollama`：用于本地提供 Battery Model，例如 `gemma4:31b`  
  链接：[https://ollama.com/](https://ollama.com/)

推荐环境：

- Windows + PowerShell
- 适合本地训练的 NVIDIA GPU，例如 `RTX 5090`
- 安装了 `torch`、`transformers`、`peft` 的 Python 环境

---

## 核心思想：Token 资产化

在传统 API 模式下，Token 是一次性消耗的燃料。

在 `Lume Treasury` 里，Token 被视为对本地智力资产的投资。

- `Shadow Mode`：捕捉真实云端返回的对话、启动指导、执行轨迹、补丁事件和工具输出
- `Intelligence Backflow`：将付费获得的云端能力蒸馏成数据集、记忆结构和 LoRA 适配器
- `Execution Feedback`：根据真实任务结果判断什么应该被强化、保留或剔除
- `Asset Reuse`：一旦模式被本地吸收，重复工作优先交给本地模型处理

目标很简单：每一次昂贵的云端调用，都应该给本地留下持续收益。

---

## Battery Model

`Battery Model = Gemma4 31B + Sentinel-LoRA`

Battery Model 是 `Lume Treasury` 的离线续航核心，也是低延迟本地接管层。

- `Base`：通过 `Ollama` 本地运行的 `Gemma4 31B`
- `Adapter`：由真实云端会话、启动指导、执行轨迹和代码产物蒸馏得到的 `Sentinel-LoRA`
- `Role`：在云端不可达、成本过高或没有必要时继续接管高频任务
- `SOH (State of Health)`：通过持续放电式测试评估本地模型与强云端基线之间的对齐程度

这就是 `Lume Treasury` 对“数字主权”的工程化表达：你用过的云端智能，会不断沉淀为本地节点的长期能力。

---

## 精选文章

### Intellectual Sovereignty: How Lume Turns Every AI Chat into a Permanent Asset

我们正在经历一种“算力殖民”。你付费提问，云端模型变得更强，而你只留下账单和一次性结果。`Lume Treasury` 提出的方向相反：每一次高价值云端交互，都应该成为你本地智能资产的一次投资。

想象一下，你与前沿模型的深度对话，可以在后台被静默复制、结构化并蒸馏成你机器上的一个“影子脑”。它会记住你的编码风格、推理偏好和工作方式，并在下一次任务中继续发挥作用，而不是随会话一起消失。

#### 从一次性 Token 到永久资产

在默认 API 经济里，Token 是燃料；在 `Lume Treasury` 里，Token 是资本开支。

- `Silent Capture`：`Shadow Logging` 不只记录最终答案，也记录规划步骤、决策分叉、修正过程和工具输出
- `Asymmetric Distillation`：`Sentinel-LoRA` 从云端轨迹中提取紧凑、可复用的任务逻辑，而不是试图复制整套云端模型
- `Battery Model`：`Gemma4 31B + Sentinel-LoRA` 构成离线续航层，在云端不可用、成本过高或没有必要时接管工作

#### 状态健康度

`Lume Treasury` 把“本地模型是否诚实可靠”当作一个工程问题来处理。`SOH` 通过反复放电式评估对照更强基线，而真实执行反馈会继续追问：代码是否真的运行？输出是否站得住？任务是否真的成功？

这能让本地模型尽量贴近现实，而不是只会产出看起来漂亮的文字。

#### 结论

`Lume Treasury` 不只是一个工具链，它也是一种关于数字主权的立场。

它试图把租来的云端智能，转化为你真正拥有的本地能力，让用户从“AI 租户”逐步变成“智能资产所有者”。

**项目信息**

- Organization: `Oepn-Lume`
- GitHub: [https://github.com/Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- Core Tenets: `Local-first AI`、`Token Assetization`、`Digital Sovereignty`
- Email: `dspwatch@gmail.com`
- Source inspiration: [X post by @wuyifree](https://x.com/wuyifree/status/2042179788329341352)

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

---

## 项目布局

- `configs/`：模型、路由与保留策略配置
- `data/`：原始日志、生成语料、训练集、营销产物和蒸馏检查点
- `docs/`：白皮书、实施方案和 Battery Model 文档
- `scripts/`：数据构建、训练、评估、同步、发布和营销入口
- `src/lume/logging/`：影子日志与 Codex 会话导入
- `src/lume/distill/`：对话、执行、历史代码蒸馏模块
- `src/lume/execution/`：运行时包装器和云端/本地执行桥接层
- `src/lume/memory/`：Wiki 记忆构建器
- `src/lume/routing/`：云端与本地路径之间的路由规则

---

## 当前工作流水线

当前最小可运行闭环是：

`Codex sessions / task runs -> raw logs -> datasets -> LoRA training -> Gemma4 Battery Model generation/evaluation`

当前偏生产的推荐栈：

- 本地基座模型：`gemma4:31b`
- 本地提供方：`Ollama`
- 当前 LoRA 候选：`data/distilled/transformers-lora-v2-realcloud/adapter`
- 真实云端语料层：
  - `real_cloud_dialogue_sft.jsonl`
  - `real_cloud_bootstrap_sft.jsonl`
  - `real_cloud_full_fidelity_sft.jsonl`
  - `real_code_execution_sft.jsonl`

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

---

## 开发者承诺

- `Privacy First`：原始用户数据默认应保留在本地
- `Execution over Theater`：所有能力都应由日志、数据集、测试和检查点支撑
- `Hardware Equity`：面向 `RTX` 和 `Apple Silicon` 等现实本地硬件路径优化
- `Low-Anxiety Operations`：提供守望者报告，而不是制造信息洪流

---

## 联系方式

- Release contact: `dspwatch@gmail.com`
- Organization: [Oepn-Lume](https://github.com/Oepn-Lume)
