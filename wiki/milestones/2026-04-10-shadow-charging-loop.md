# 2026-04-10 Shadow Charging Loop

## What Changed

- Added a formal `Diurnal Shadow-Charging` workflow so daytime shadow logging and nighttime training are no longer mixed together.
- Added a lightweight shadow-charge ledger builder that turns task runs into append-only charging assets.
- Added a night-watch charging runner that checks idle time, charging status, CPU pressure, and charging window before launching retraining.
- Added a new launcher mode so the repo can run the charging flow directly from `python main.py charge`.

## Why It Matters

This is the first step toward making the Battery Model evolve on a real day/night rhythm:

- daytime stays close to zero-interference logging
- nighttime turns accumulated traces into retraining assets
- charging only starts when the local machine is idle and power-safe

That makes the system closer to the intended "shadow by day, entity by night" operating principle.

## Key Files

- `src/lume/charging/policy.py`
- `src/lume/charging/ledger.py`
- `scripts/build_shadow_charge_ledger.py`
- `scripts/run_shadow_charging.py`
- `main.py`
- `README.md`
- `README.zh-CN.md`

## Validation

- Charging policy unit tests cover allowed and blocked device states.
- Ledger generation test covers append-only extraction from task runs.
- Smoke runs produce a ledger and a night charging report without modifying the daytime pipeline.
