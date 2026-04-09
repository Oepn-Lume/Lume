"""Route a task into cloud, hybrid, or local mode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.routing import route_task


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument(
        "--routing-config",
        default=str(ROOT / "configs" / "routing.yaml"),
    )
    parser.add_argument(
        "--task-runs-root",
        default=str(ROOT / "data" / "task_runs"),
    )
    parser.add_argument(
        "--local-quality-config",
        default=str(ROOT / "configs" / "local_quality.json"),
    )
    parser.add_argument("--privacy-sensitive", action="store_true")
    parser.add_argument("--cloud-unavailable", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decision = route_task(
        args.task,
        routing_config_path=Path(args.routing_config),
        task_runs_root=Path(args.task_runs_root),
        cloud_available=not args.cloud_unavailable,
        privacy_sensitive=args.privacy_sensitive,
        local_quality_path=Path(args.local_quality_config),
    )
    payload = {
        "decision": decision.to_dict(),
        "local_quality_config": str(Path(args.local_quality_config)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
