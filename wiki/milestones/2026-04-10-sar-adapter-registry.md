# 2026-04-10 SAR Adapter Registry

## What Changed

- Refactored SAR export into an adapter registry.
- Added a default `SoftwareTaskRunAdapter` for current `task_runs`.
- Updated the SAR protocol document to describe the adapter contract and extension path.

## Why It Matters

This makes SAR extensible by design instead of software-task-specific by accident.

- future domains can plug into the same export pipeline
- the protocol remains stable while extraction logic can vary by domain
- Battery Model 2.0 is now closer to a reusable cross-agent standard interface

## Key Files

- `src/lume/spi/adapters.py`
- `src/lume/spi/sar_dataset.py`
- `src/lume/spi/__init__.py`
- `tests/test_sar_protocol.py`
- `docs/sar-protocol-v1.md`

## Validation

- Added adapter and registry coverage in SAR protocol tests.
- Regenerated `sar_protocol.jsonl` through the main CLI entry.
- Rebuilt wiki entries so the protocol and milestone updates are indexed.
