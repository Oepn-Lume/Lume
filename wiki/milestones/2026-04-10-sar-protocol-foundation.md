# 2026-04-10 SAR Protocol Foundation

## What Changed

- Added a standardized `State-Action-Reward` protocol layer for Battery Model 2.0.
- Added protocol envelopes for state, action, and reward so future agents can integrate through a common interface instead of code-specific assumptions.
- Added a SAR dataset exporter from existing `task_runs`.
- Wired the SAR dataset into the standard distillation dataset build path.
- Added a top-level `python main.py sar` entry so the protocol dataset can be generated as a first-class workflow rather than only as an internal builder step.

## Why It Matters

This is the first practical step toward making the Battery Model behave like a reusable intelligence standard rather than a single software-agent patch.

- task runs can now be re-expressed as generic state/action/reward records
- future agents only need to provide state, action, and feedback signals to participate
- the repo now has a protocol-shaped artifact that can evolve toward robotics, edge devices, and non-code agent domains

## Key Files

- `src/lume/spi/protocol.py`
- `src/lume/spi/sar_dataset.py`
- `scripts/build_sar_dataset.py`
- `src/lume/distill/dataset.py`
- `tests/test_sar_protocol.py`

## Validation

- Added a protocol dataset unit test with a synthetic task run.
- The SAR dataset is now generated through the normal dataset build flow.
- Confirmed direct export through `scripts/build_sar_dataset.py`.
- Confirmed user-facing export through `python main.py sar`.
