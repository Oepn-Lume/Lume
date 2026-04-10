# 2026-04-10 Codex Action Taxonomy

## What Changed

- Added a Codex action taxonomy for software worksite commands such as continue, patch, log inspection, status, and publish.
- Added a dedicated Codex action dataset builder.
- Wired Codex action readiness into the routing quality snapshot and routing decision logic.

## Why It Matters

This pushes the Battery Model toward “keep working” behavior instead of general chat behavior.

- short software commands now map to explicit action labels
- the local model can be evaluated on engineering-action readiness, not only generic perplexity
- routing can keep more Codex-like work local when action readiness improves

## Key Files

- `src/lume/codex/action_taxonomy.py`
- `src/lume/distill/codex_actions.py`
- `src/lume/evaluation/quality_snapshot.py`
- `src/lume/routing/rules.py`
- `tests/test_codex_actions.py`
- `tests/test_routing.py`

## Validation

- Added taxonomy classification tests.
- Added Codex action dataset generation tests.
- Added routing coverage for high and low Codex action readiness.
- Wired the dataset into default training data loading.
