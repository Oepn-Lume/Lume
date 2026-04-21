---
title: Agent Augmentation Higher Grade Roadmap
section: analysis
updated_at: 2026-04-21T00:00:00Z
status: roadmap
---

# Higher-grade roadmap

## Current baseline

The current settled state is:

- `Codex + Lume = B`
- `OpenClaw + Lume = stable B-`
- `Claude Code + Lume = stable B-`

## Next higher-grade goals

### Goal A: raise `Codex` from `B` toward `A`

What blocks it now:

- baseline grounding quality on newer rows
- not enough cleanup on the remaining caveat-heavy parts of the line
- not enough reason yet to say caveats no longer change the bottom-line judgment

What would move it:

- replace more proxy-heavy baseline rows with stronger grounded baselines
- keep the harder families positive under stricter accounting
- make the newest rows as clean as the older core

### Goal B: raise `OpenClaw` from `stable B-` toward `B`

What blocks it now:

- sample count is still small
- even though grounding is now solid, the line still needs more volume and less early-line feel

What would move it:

- more grounded rows beyond the current stable core
- more repetition without softening the current four-metric shape
- enough growth that the line stops looking like a well-executed small line and starts looking like a strong line

### Goal C: raise `Claude Code` from `stable B-` toward `B`

What blocks it now:

- the line has only just cleared the breadth threshold
- it still needs a little more density in the third family and more overall maturity

What would move it:

- deepen the new third family
- keep all three families positive under added grounded rows
- reduce the sense that the line only recently crossed the threshold

## Program-level priority order

Recommended next order:

1. ship the current release package cleanly
2. deepen `OpenClaw` and `Claude Code` so both `stable B-` lines become harder to dismiss
3. then decide whether the best marginal value is:
   - `Codex -> A`
   - or `OpenClaw / Claude Code -> B`

## Plain-language version

The next phase is not about proving `Lume` works at all. That part is done.

The next phase is about making the current three-line result cleaner, harder to argue against, and strong enough that the grades move up without sounding inflated.
