# 2026-04-10 Robotics SAR Adapter

## What Changed

- Added a second SAR domain adapter for robotics-style traces.
- Registered the robotics adapter ahead of the default software adapter in the SAR registry.
- Extended SAR tests to cover a motion-command record.

## Why It Matters

This is the first real step from software-only SAR toward a cross-domain Battery Model interface.

- Battery Model 2.0 now has a concrete non-software adapter path
- robotics-style traces can be mapped into the same protocol surface
- the registry pattern is now proven to support multiple domains, not just promised in docs

## Key Files

- `src/lume/spi/adapters.py`
- `src/lume/spi/__init__.py`
- `tests/test_sar_protocol.py`
- `docs/sar-protocol-v1.md`
- `README.md`

## Validation

- Added a robotics adapter smoke test with `robot_trace.json`.
- Regenerated `sar_protocol.jsonl` through `python main.py sar`.
- Rebuilt wiki entries so the new milestone and protocol changes are indexed.
