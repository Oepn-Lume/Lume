from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class PostDraft:
    order: int
    theme: str
    body: str


def default_thread(repo_url: str) -> List[PostDraft]:
    return [
        PostDraft(
            order=1,
            theme="pain_point",
            body=(
                "You do not need to keep paying intelligence rent forever. "
                "Lume turns high-value cloud usage into local capability assets."
            ),
        ),
        PostDraft(
            order=2,
            theme="battery_model",
            body=(
                "Battery Model = Gemma4 31B + LoRA. "
                "Shadow logging captures real cloud guidance, then distillation turns it into local continuity."
            ),
        ),
        PostDraft(
            order=3,
            theme="invitation",
            body=(
                "Join the Starfire Protocol. Build private memory, reusable local inference, "
                f"and open contribution loops around Lume. {repo_url}"
            ),
        ),
    ]


def render_watchman_report(posts: List[PostDraft], repo_url: str, dry_run: bool) -> str:
    credentials_ready = bool(os.getenv("X_API_KEY") and os.getenv("X_API_SECRET"))
    lines = [
        "# Watchman Report",
        "",
        f"- Dry run: {'yes' if dry_run else 'no'}",
        f"- Repository URL: {repo_url}",
        f"- Draft posts prepared: {len(posts)}",
        f"- X credentials detected: {'yes' if credentials_ready else 'no'}",
    ]
    if not credentials_ready:
        lines.append("- Status: preview-only mode; no outbound post was attempted.")
    else:
        lines.append("- Status: credentials present; ready for explicit posting flow.")
    lines.append("")
    lines.append("## Draft Thread")
    for post in posts:
        lines.append(f"{post.order}. [{post.theme}] {post.body}")
    return "\n".join(lines) + "\n"


def write_outputs(posts: List[PostDraft], report: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    drafts_path = output_dir / "x_thread_drafts.json"
    report_path = output_dir / "watchman_report.md"
    drafts_path.write_text(
        json.dumps([asdict(post) for post in posts], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare Starfire launch-thread drafts and a watchman report."
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/YourRepo/Lume",
        help="Repository URL to include in invitation copy.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/marketing/starfire_launch",
        help="Directory for generated drafts and reports.",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Reserved for future live posting. Current implementation still writes previews only.",
    )
    args = parser.parse_args()

    posts = default_thread(args.repo_url)
    dry_run = True
    report = render_watchman_report(posts, args.repo_url, dry_run=dry_run)
    write_outputs(posts, report, Path(args.output_dir))
    print(report)
    if args.post:
        print("Live posting is not enabled in this build; preview artifacts were generated instead.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
