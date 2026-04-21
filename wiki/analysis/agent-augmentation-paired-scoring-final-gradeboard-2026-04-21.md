---
title: Agent Augmentation Paired Scoring Final Gradeboard
section: analysis
updated_at: 2026-04-21T00:00:00Z
status: crossline_gradeboard
---

# Final gradeboard

Framing fixed as:

- `Codex baseline vs Codex + Lume`
- `OpenClaw baseline vs OpenClaw + Lume`
- `Claude Code baseline vs Claude Code + Lume`

## Grade scale

- `A`: externally robust, low-caveat, strong baseline grounding
- `B`: strong usable evidence, caveats remain but not dominant
- `C`: usable directional evidence, caveats are still meaningful
- `D`: early signal only, fragile or sparse
- `E`: insufficient evidence

## Final current grades

| line | current version | ledger total | temporary grade | read |
| --- | --- | ---: | --- | --- |
| `Codex baseline vs Codex + Lume` | `v4` | `31` | `B` | `strong usable evidence` |
| `OpenClaw baseline vs OpenClaw + Lume` | `v6` | `10` | `stable B-` | `stable, grounded, and externally explainable` |
| `Claude Code baseline vs Claude Code + Lume` | `v6` | `10` | `stable B-` | `stable after third-family grounding landed` |

## Why Codex is highest

- largest ledger
- deepest version history
- strongest current right to make a directional external claim

Main reason it is not `A`:

- baseline-grounding quality still needs more cleanup on newer rows

## Why OpenClaw is now `stable B-`

- grounded baseline rows reached `7`
- grounded family coverage reached `3 / 3`
- the line is no longer mainly supported by proxy-only reading

## Why Claude Code is now `stable B-`

- grounded baseline rows reached `9`
- the third family `env_binding` now has more than a single decorative foothold
- the line is no longer blocked mainly by breadth

## External-claim policy

These are safe now:

- `Codex baseline vs Codex + Lume` has strong usable paired evidence
- `OpenClaw baseline vs OpenClaw + Lume` has reached `stable B-`
- `Claude Code baseline vs Claude Code + Lume` has reached `stable B-`

These should still be avoided:

- claiming any of the three lines are already publication-clean or final-grade
- claiming `Codex` has already reached `A`
