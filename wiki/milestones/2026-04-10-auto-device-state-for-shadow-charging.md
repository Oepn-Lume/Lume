# 2026-04-10 Auto Device State for Shadow Charging

## What Changed

- Added automatic Windows device-state detection for the shadow charging loop.
- The night-side charging runner now detects idle time and charging state by default instead of requiring manual flags.
- Charging reports now include the detected state source so the workflow is auditable.

## Why It Matters

This turns `python main.py charge` into a much more realistic operator entrypoint.

- the user no longer has to simulate charging conditions by hand
- the night watch flow can react to real local conditions
- the Battery Model’s day/night rhythm becomes closer to the intended production behavior

## Key Files

- `src/lume/charging/system_state.py`
- `src/lume/charging/__init__.py`
- `scripts/run_shadow_charging.py`
- `main.py`
- `tests/test_shadow_charging.py`

## Validation

- Override-based detection test added for deterministic local validation.
- Existing charging policy and ledger tests still pass.
- Shadow charging reports now record `detection_source` metadata.
