# 2026-04-10 SAR Spec Definition

## What Changed

- Formalized `SAR` as a protocol specification rather than only a dataset exporter.
- Added explicit protocol versioning, domain enums, agent enums, and action enums.
- Added runtime validation rules for `SAR` record construction.
- Added a dedicated protocol document for repository-visible reference.

## Why It Matters

This turns Battery Model 2.0 from an internal software-agent data format into a reusable interface contract.

- future agent types can target a known schema
- versioning and validation reduce accidental protocol drift
- the repo now has a stable specification that can be cited by runtime, dataset, and future cross-device work

## Key Files

- `src/lume/spi/protocol.py`
- `src/lume/spi/__init__.py`
- `src/lume/spi/sar_dataset.py`
- `docs/sar-protocol-v1.md`
- `tests/test_sar_protocol.py`

## Validation

- Added protocol validation tests for valid and invalid domains.
- Regenerated `sar_protocol.jsonl` through the CLI entry.
- Rebuilt wiki entries so the protocol document is indexed in repository memory.
