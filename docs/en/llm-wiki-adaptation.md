# LLM Wiki Adaptation

`Lume` adapts the `llm-wiki` idea into a local memory layer that sits between raw logs and training datasets.

## Mapping

- raw sources -> `data/raw_logs/` and `data/task_runs/`
- wiki pages -> `data/wiki/tasks/`
- index -> `data/wiki/index.md`
- log -> `data/wiki/log.md`

## Purpose

- preserve durable knowledge beyond chat context
- convert tasks into structured pages
- create a bridge between execution history and future training

## Current Limitation

The current wiki is task-centric. It still needs richer topic pages such as users, workflows, decisions, and reusable patterns.
