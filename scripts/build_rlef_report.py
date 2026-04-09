"""Summarize reward and preference datasets produced by the RLEF pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets-root",
        default=str(ROOT / "data" / "datasets"),
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "distilled" / "rlef"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets_root = Path(args.datasets_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    reward_records = _read_jsonl(datasets_root / "rlef_reward.jsonl")
    preference_records = _read_jsonl(datasets_root / "rlef_preference.jsonl")
    rewards = [float(record.get("reward", 0.0)) for record in reward_records]
    route_modes: dict[str, int] = {}
    for record in reward_records:
        route = str(record.get("metadata", {}).get("route_mode", "unknown"))
        route_modes[route] = route_modes.get(route, 0) + 1

    payload = {
        "reward_record_count": len(reward_records),
        "preference_record_count": len(preference_records),
        "reward_mean": statistics.mean(rewards) if rewards else None,
        "reward_min": min(rewards) if rewards else None,
        "reward_max": max(rewards) if rewards else None,
        "route_mode_distribution": route_modes,
    }
    report_json = output_root / "rlef_report.json"
    report_md = output_root / "rlef_report.md"
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")
    report_md.write_text(
        "\n".join(
            [
                "# RLEF Report",
                "",
                f"- Reward records: {payload['reward_record_count']}",
                f"- Preference records: {payload['preference_record_count']}",
                f"- Reward mean: {payload['reward_mean']}",
                f"- Reward min: {payload['reward_min']}",
                f"- Reward max: {payload['reward_max']}",
                f"- Route modes: {json.dumps(route_modes, ensure_ascii=False)}",
                "",
            ]
        ),
        "utf-8",
    )
    print(report_json)
    print(report_md)


if __name__ == "__main__":
    main()
