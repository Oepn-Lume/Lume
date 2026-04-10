---
id: milestone-logging-rule-2026-04-10
type: milestone
updated_at: 2026-04-10T00:00:00Z
---

# 2026-04-10 Milestone Logging Rule

## What Happened

A new repository-level rule was established: every milestone implementation action performed in `Lume Treasury` must be written as a wiki record.

## Why It Matters

This turns milestone progress into durable project memory instead of leaving it scattered across commit history and chat threads. It also makes the wiki a true engineering ledger, not just a documentation mirror.

## Files and Modules

- `src/lume/memory/wiki.py`
- `wiki/memory/assistant-operating-memory.md`
- `wiki/milestones/2026-04-10-milestone-logging-rule.md`

## Validation

- extended wiki generation to discover and list `milestones/` pages
- extended wiki generation to discover and list `memory/` pages
- confirmed the wiki can now surface both categories in `wiki/index.md` and `wiki/log.md`

## GitHub Status

This milestone should be committed and pushed together with the updated wiki index and log so the rule becomes part of the repository-visible history.
