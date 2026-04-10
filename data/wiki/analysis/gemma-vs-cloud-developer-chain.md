---
id: gemma-vs-cloud-developer-chain
type: analysis
section: gemma-vs-cloud
---

# Developer and Codex Internal Message Gap

## Summary
The replay set includes developer/codex-to-cloud turns, exposing a second gap: Gemma does not yet read internal workflow signals the way the cloud model does.

## Details
- Prompt role counts: {'user': 727, 'developer': 56}
- Internal command approvals, repo-state updates, and execution control messages are often treated by Gemma as plain text rather than workflow state.
- This is a key training direction for turning a local model into a collaborative runtime agent instead of a standalone chat assistant.

