# 🪙 Lume Treasury：你的私人智力金库

> **云端对话，本地储蓄。别再消费 AI，去拥有它。**

英文版请看 [README.md](./README.md)。

**Lume Treasury** 是一个本地优先的 AI 系统，目标是把高价值的云端对话和推理过程，沉淀成你自己可以长期持有的本地智能资产。

在传统的 Token 经济里，你一次次付费调用模型，模型平台越来越强，而你只留下账单。`Lume Treasury` 想做的事情正相反：**把每一次高价值云端交互，都变成你本地“智力金库”的增量储备。**

---

## 运行条件

开始使用 `Lume Treasury` 之前，需要先在本地安装这两个组件：

- **Codex**：作为本地执行与编码运行时  
  链接：[https://openai.com/codex/](https://openai.com/codex/)
- **Ollama**：用于本地提供 Battery Model，比如 `gemma4:31b`  
  链接：[https://ollama.com/](https://ollama.com/)

---

## 💎 核心观点：Token 不是消耗品，而是资产

在默认 API 模式下，Token 像燃料一样烧掉就没了。

在 **Lume Treasury** 里，Token 被视为对私人智能资产的投入。

- **Shadow Mode**：静默记录云端推理、工具输出和执行轨迹
- **Intelligence Backflow**：把昂贵的云端逻辑蒸馏成你自己的 LoRA 适配器
- **Execution Feedback**：根据真实任务结果，比如“代码有没有跑通”，来强化本地模型
- **Asset Reuse**：一旦某种模式被本地吸收，后续相似任务就优先由本地模型接管，节省成本和延迟

---

## 🔋 Battery Model（Gemma4 + Sentinel-LoRA）

**Battery Model** 是 Lume 的离线续航核心。它不只是一个模型，而是一项会持续增长的本地资产。

- **Base**：通过 `Ollama` 运行的 `Gemma4 31B`
- **Adapter**：`Sentinel-LoRA`，从你的真实云端会话、编码风格和执行轨迹中蒸馏得到
- **SOH（State of Health）**：衡量本地模型相对于强云端基线是否仍然健康、稳定、对齐
- **目标**：你每用一次云端，本地节点就更强一点。数字主权从这里开始。

---

## 🧠 为什么要做 Lume？

我们正在经历一种“算力殖民”：

你付费调用模型，平台拿走数据和收益，而你拿到的是一次性的回答。

`Lume Treasury` 要做的是把这个逻辑翻过来：

1. **静默捕捉**：记录规划步骤、决策分叉、修正过程和隐藏的执行逻辑
2. **非对称蒸馏**：不是复制整个云端模型，而是提取你真正会反复用到的逻辑
3. **本地觉醒**：让你的电脑不再只是一个终端，而是逐渐成为一个懂你、会做事的本地伙伴

---

## 🚀 工作流水线：持续进化的闭环

Lume 当前的最小闭环是：

1. **Capture**：记录真实的 Codex 与云端轨迹
2. **Synthesize**：构建高保真蒸馏数据集（`jsonl`）
3. **Train**：执行本地 LoRA 训练
4. **Route**：让系统自动判断“这个任务现在能不能交给本地 Battery Model”

---

## 🛠 项目进度与里程碑

| 功能 | 说明 | 状态 |
| :--- | :--- | :--- |
| **Shadow Logging** | 记录工具调用、任务产物和云端可见推理轨迹 | ✅ |
| **LLM Wiki Memory** | 把任务运行结果沉淀成可复用的结构化记忆页面 | ✅ |
| **Battery Routing** | 根据复杂度和本地质量在云端与本地之间切换 | ✅ |
| **Battery Model Runtime** | 通过 `Ollama` 运行 `gemma4:31b` 作为本地规划层 | ✅ |
| **LoRA Training** | 在本地硬件上进行 PEFT 训练 | ✅ |
| **Evaluation Reports** | 保存质量快照、评估报告和历史结果 | ✅ |
| **Hybrid Refinement Logging** | 记录本地草稿与云端精修之间的结构化差异 | ✅ |
| **RLEF Layer** | 基于真实执行反馈的数据集和最小偏好优化链路 | 🏗️ 开发中 |
| **Continuous Retraining** | 自动化 `Build -> Train -> Evaluate -> Route` 周期 | 📅 计划中 |

---

## 🤝 开发者承诺

- **Privacy First**：原始数据默认保留在本地
- **Execution over Theater**：所有能力都应该有日志、数据集、测试或检查点支撑
- **Hardware Equity**：优先适配用户真正拥有的硬件
- **Low-Anxiety Ops**：提供守望者报告，而不是制造信息洪流

---

## 📬 联系方式

- **GitHub**：[Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- **Email**：`dspwatch@gmail.com`
- **理念来源**：围绕 “Token Assetization” 这条核心命题持续推进
