---
id: llm-wiki-adaptation-md
type: doc
relative_path: llm-wiki-adaptation.md
language: mixed
section: root
---

# LLM Wiki Adaptation

## Source
- Path: `llm-wiki-adaptation.md`
- Language: `mixed`
- Section: `root`
- Original file: [llm-wiki-adaptation.md](C:/Users/yh-PC-003/Desktop/codex/lume/docs/llm-wiki-adaptation.md)

## Body

# LLM Wiki Adaptation

## English

`Lume` adapts the `llm-wiki` idea into a local memory layer that sits between raw logs and training datasets.

### Mapping

- raw sources -> `data/raw_logs/` and `data/task_runs/`
- wiki pages -> `data/wiki/tasks/`
- index -> `data/wiki/index.md`
- log -> `data/wiki/log.md`

### Purpose

- preserve durable knowledge beyond chat context
- convert tasks into structured pages
- create a bridge between execution history and future training

### Current Limitation

The current wiki is task-centric. It still needs richer topic pages such as users, workflows, decisions, and reusable patterns.

## 中文

`Lume` 将 `llm-wiki` 的思路改造为一个位于原始日志与训练数据之间的本地记忆层。

### 映射关系

- 原始来源 -> `data/raw_logs/` 与 `data/task_runs/`
- Wiki 页面 -> `data/wiki/tasks/`
- 索引 -> `data/wiki/index.md`
- 日志 -> `data/wiki/log.md`

### 目的

- 在聊天上下文之外保存长期知识
- 把任务转成结构化页面
- 在执行历史与未来训练之间建立桥梁

### 当前限制

当前 Wiki 仍以任务页为中心，后续还需要补充用户页、工作流页、决策页与可复用模式页。

