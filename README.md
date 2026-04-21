# Lume

> Lume is not a replacement agent. It is an augmentation layer that helps existing agents make fewer repeated mistakes, waste less budget, and reroute faster after failure.

## Public Release Snapshot

The current before/after result is now stable across three agent lines:

| Line | Current Grade | Read |
| --- | --- | --- |
| `Codex baseline` vs `Codex + Lume` | `B` | strongest line, already a strong usable result |
| `OpenClaw baseline` vs `OpenClaw + Lume` | `stable B-` | stable, grounded, and externally explainable |
| `Claude Code baseline` vs `Claude Code + Lume` | `stable B-` | stable after third-family grounding landed |

This means the project is no longer in a "one strong demo" state. It now has one `B` line plus two `stable B-` lines.

## What Lume Is

Lume is a:

- failure-aware control layer
- rerouting layer
- anti-stall / anti-loop layer
- paired evaluation surface for `baseline` vs `baseline + Lume`

Lume is **not**:

- a standalone replacement for `Codex`, `OpenClaw`, or `Claude Code`
- a claim of final-grade or publication-clean proof
- a claim that all three lines are equally strong

## Current External Wording

The safe public wording right now is:

> Lume adds a control layer on top of existing agents, and the current cross-line result is now stable across three lines: `Codex + Lume = B`, `OpenClaw + Lume = stable B-`, and `Claude Code + Lume = stable B-`.

## Evidence Anchors

Use these pages as the release-time source of truth:

- Phase close:
  [wiki/analysis/agent-augmentation-phase-close-note-2026-04-21.md](./wiki/analysis/agent-augmentation-phase-close-note-2026-04-21.md)
- Final inventory:
  [wiki/analysis/agent-augmentation-final-inventory-2026-04-21.md](./wiki/analysis/agent-augmentation-final-inventory-2026-04-21.md)
- Final gradeboard:
  [wiki/analysis/agent-augmentation-paired-scoring-final-gradeboard-2026-04-21.md](./wiki/analysis/agent-augmentation-paired-scoring-final-gradeboard-2026-04-21.md)
- Public release summary:
  [wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md](./wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md)
- Public summary strip:
  [wiki/analysis/lume-public-summary-strip-final-2026-04-21.md](./wiki/analysis/lume-public-summary-strip-final-2026-04-21.md)

## Wiki

The repository wiki is versioned inside the repo.

- Wiki index:
  [wiki/index.md](./wiki/index.md)
- Public release hub:
  [wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md](./wiki/analysis/agent-augmentation-public-release-summary-2026-04-21.md)

## Release Boundary

What can be said now:

- Lume improves multiple agent lines, not just one showcase runtime
- the current result is one `B` line plus two `stable B-` lines
- all three lines now have formal before/after scoring pages

What should still be said carefully:

- this is not yet publication-clean evidence
- `Codex` has not yet reached `A`
- `stable B-` means stable and externally explainable, not finished

## Next Higher-Grade Goals

The next-stage higher-grade roadmap is:

- `Codex: B -> A`
- `OpenClaw: stable B- -> B`
- `Claude Code: stable B- -> B`

Roadmap:
[wiki/analysis/agent-augmentation-higher-grade-roadmap-2026-04-21.md](./wiki/analysis/agent-augmentation-higher-grade-roadmap-2026-04-21.md)

## Contact

- GitHub: [Oepn-Lume/Lume](https://github.com/Oepn-Lume/Lume)
- Email: `dspwatch@gmail.com`
