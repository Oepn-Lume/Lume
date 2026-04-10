# V3 -> V4 Iteration Plan

## Purpose

This document turns the current `v3-restored` findings into an execution plan for `v4`.

The main conclusion from the current comparison is:

- `v3-restored` is materially stronger than the current `transformers-lora-cycle` baseline
- the biggest remaining weakness is `continue_task`
- routing confidence is improving, but the project still lacks a strong enough continue-task profile to safely expand local takeover across all software actions

Relevant reports:

- [`data/reports/v3_vs_cycle_2026-04-10.md`](C:/Users/yh-PC-003/Desktop/codex/lume/data/reports/v3_vs_cycle_2026-04-10.md)
- [`data/reports/v3_eval_2026-04-10.md`](C:/Users/yh-PC-003/Desktop/codex/lume/data/reports/v3_eval_2026-04-10.md)
- [`data/reports/v3_local_quality_snapshot_2026-04-10.json`](C:/Users/yh-PC-003/Desktop/codex/lume/data/reports/v3_local_quality_snapshot_2026-04-10.json)

## Current V3 Summary

### Strengths

- Strong improvement over the current cycle baseline on training loss and perplexity
- Stronger bootstrap, full-fidelity, and code-execution evaluation results
- Adaptive routing score now exceeds the current adaptive threshold
- Patch/log-style action performance is meaningfully better than the current baseline

### Weaknesses

- `continue_task` remains the weakest software-action category
- Character-level matching remains low even when perplexity improves
- Current evaluation still uses a very small sample count in critical comparisons
- The main routing config still points to the old baseline, not to `v3-restored`

## V4 Objectives

V4 should not be treated as "just retrain V3 with more data". It should explicitly target the current bottlenecks.

Primary objectives:

1. Raise `continue_action_readiness` from `0.205` to at least `0.35-0.45`
2. Preserve or improve current `patch` and `log` action readiness
3. Increase evaluation stability so version-to-version comparisons are decision-grade
4. Produce a candidate routing snapshot for V4 without immediately overwriting the current production snapshot

## Target Metrics

These are suggested V4 target ranges, not hard guarantees.

| Metric | Current V3 | Target V4 |
| --- | ---: | ---: |
| `local_quality_score` | `0.456` | `0.50+` |
| `adaptive_local_quality_score` | `0.609` | `>= 0.60` |
| `continue_action_readiness` | `0.205` | `0.35-0.45` |
| `codex_continue_perplexity` | `21.60` | `< 15` |
| `patch_action_readiness` | `0.451` | `>= 0.45` |
| `log_action_readiness` | `0.415` | `>= 0.41` |

## Workstreams

### 1. Expand Continue-Task Data

Goal:
Improve the model's ability to continue an in-progress software task from current state rather than restarting or drifting into generic advice.

Why:
`continue_task` is currently the clearest weak spot in V3.

Code surfaces:

- [`src/lume/distill/codex_actions.py`](C:/Users/yh-PC-003/Desktop/codex/lume/src/lume/distill/codex_actions.py)
- [`data/task_runs`](C:/Users/yh-PC-003/Desktop/codex/lume/data/task_runs)

Actions:

1. Expand task-run-derived continue examples beyond the current minimal augmentation
2. Include stronger state summaries where available:
   - previous goal
   - last assistant action
   - notes summary
   - route mode
   - recent artifact or file summary
3. Filter low-value continue samples that are too short, too generic, or missing usable state
4. Keep continue-task examples distinct from generic short-command action examples

Exit criteria:

- `codex_continue_eval`-related sources are noticeably larger and higher quality
- continue-task prompts look stateful rather than keyword-only

### 2. Rebalance Training Mixture

Goal:
Prevent action-task weaknesses from being drowned out by larger general SFT pools.

Why:
Current training strength is broad, but not well balanced across action classes.

Code surface:

- [`src/lume/distill/train.py`](C:/Users/yh-PC-003/Desktop/codex/lume/src/lume/distill/train.py)

Actions:

1. Introduce weighted or repeated sampling for weaker action-task sources
2. Increase the effective share of:
   - codex action records
   - continue-task records
   - developer chain records
   - historical workspace code records
3. Keep patch/log data sufficiently represented so V4 does not regress there
4. If direct weighted sampling is too invasive, build a merged rebalanced dataset before training

Exit criteria:

- V4 training input is intentionally rebalanced rather than passively file-ordered
- continue/action data has a clearly higher effective contribution

### 3. Add Continue-Focused Preference Optimization

Goal:
Use preference-style learning to improve the quality of "next useful step" behavior for active tasks.

Why:
LoRA improves general capability, but continue-task quality often depends on preferring the right continuation over a merely plausible one.

Code surfaces:

- [`src/lume/rl/dpo.py`](C:/Users/yh-PC-003/Desktop/codex/lume/src/lume/rl/dpo.py)
- [`src/lume/rl/grpo.py`](C:/Users/yh-PC-003/Desktop/codex/lume/src/lume/rl/grpo.py)

Actions:

1. Build continue-task preference pairs from real task runs
2. Define "good continuation" vs "bad continuation" criteria
3. Run a lightweight continue-specific DPO and/or GRPO pass
4. Track continue-specific preference metrics separately where possible

Suggested "good continuation" properties:

- uses current task state
- references recent artifacts or notes when relevant
- proposes the next concrete action
- stays concise and action-first

Suggested "bad continuation" properties:

- restarts from scratch
- ignores existing state
- gives only generic advice
- responds with broad explanation instead of task continuation

Exit criteria:

- continue-task preference data exists and is reproducible
- V4 continue-task readiness improves without harming patch/log readiness

### 4. Strengthen Evaluation Protocol

Goal:
Make V4 comparisons stable enough to support routing and release decisions.

Why:
Single-example evaluation is useful for direction finding, but too noisy for version decisions.

Code surfaces:

- [`scripts/evaluate_local_model.py`](C:/Users/yh-PC-003/Desktop/codex/lume/scripts/evaluate_local_model.py)
- [`scripts/update_local_quality_snapshot.py`](C:/Users/yh-PC-003/Desktop/codex/lume/scripts/update_local_quality_snapshot.py)
- [`src/lume/evaluation/quality_snapshot.py`](C:/Users/yh-PC-003/Desktop/codex/lume/src/lume/evaluation/quality_snapshot.py)

Actions:

1. Increase critical evaluation runs to at least `max_examples=8`
2. Always evaluate these categories for V4:
   - bootstrap
   - full_fidelity
   - code_execution
   - codex_action
   - codex_continue
   - codex_patch
   - codex_log
3. Save both JSON and Markdown reports
4. Avoid replacing the production snapshot until V4 is reviewed

Exit criteria:

- V4 evaluation artifacts are present and reproducible
- comparisons use enough examples to reduce one-sample noise

### 5. Produce a Candidate Routing Snapshot

Goal:
Generate a V4 routing snapshot that can be reviewed before switching the main project baseline.

Why:
The project should avoid silently changing routing behavior based on an unreviewed experiment.

Actions:

1. Write V4 quality output to a dedicated candidate snapshot first
2. Compare V4 candidate snapshot against:
   - current production snapshot
   - current cycle report
   - V3 restored report
3. Only promote V4 into [`configs/local_quality.json`](C:/Users/yh-PC-003/Desktop/codex/lume/configs/local_quality.json) after review

Promotion conditions:

- adaptive score remains above threshold
- continue readiness improves materially
- patch/log do not regress in a meaningful way
- evaluation sample size is strong enough to trust the comparison

## Recommended Execution Order

1. Expand continue-task data
2. Rebalance the SFT training mix
3. Train `v4` LoRA
4. Run continue-focused DPO and/or GRPO
5. Evaluate V4 with higher sample counts
6. Generate a candidate routing snapshot
7. Decide whether to promote V4 into the main routing config

## Deliverables

Minimum V4 deliverables:

- `v4` model directory under [`data/distilled`](C:/Users/yh-PC-003/Desktop/codex/lume/data/distilled)
- evaluation JSON report
- evaluation Markdown report
- candidate routing snapshot JSON
- comparison note against current baseline

## Decision Rule

V4 is ready to replace the current cycle baseline only if:

- it clearly outperforms the current cycle baseline
- it preserves current patch/log advantages
- it materially improves continue-task readiness
- its routing snapshot is supported by more stable evaluation coverage
