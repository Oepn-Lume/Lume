# 2026-04-10 Codex Action Readiness Routing

## What Changed

`Lume` now evaluates `continue`, `patch`, and `log` actions with separate readiness scores instead of using one shared `codex_action_readiness` gate.

## Why It Matters

The Codex Battery Model should not expand local takeover uniformly. `continue_task`, `prepare_patch`, and `inspect_log` each mature at different speeds, so routing now uses action-specific readiness to decide when a short software command can stay local.

## Key Files

- `src/lume/distill/codex_actions.py`
- `src/lume/evaluation/quality_snapshot.py`
- `src/lume/routing/rules.py`
- `configs/routing.yaml`
- `tests/test_routing.py`

## Validation

- `py_compile` on updated routing and evaluation modules
- routing smoke checks for `continue`, `patch`, and `log`
- targeted routing tests for action-specific thresholds
