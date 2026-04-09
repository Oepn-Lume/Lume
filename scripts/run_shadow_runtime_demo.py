"""Run a no-touch shadow logging demo using the observed runtime adapters."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lume.execution.runtime import ObservedRuntime, RuntimeModels


def fake_cloud_handler(prompt: str) -> str:
    return (
        "Cloud plan: collect the current task context, patch the logging layer, "
        "and persist a full session trace for distillation."
    )


def fake_codex_handler(instruction: str) -> str:
    return (
        "Codex response: applying the requested runtime patch and recording the "
        "execution artifacts automatically."
    )


def main() -> None:
    runtime = ObservedRuntime(
        task_id="no-touch-runtime-demo",
        user_goal="Prove shadow logging can run invisibly during a task.",
        route_mode="hybrid",
        output_root=ROOT / "data" / "task_runs",
        models=RuntimeModels(
            primary="gpt-cloud-demo",
            cloud="gpt-cloud-demo",
            codex="codex-demo",
        ),
        cloud_handler=fake_cloud_handler,
        codex_handler=fake_codex_handler,
        metadata={"demo": True, "thread_id": "no-touch-demo"},
    )

    runtime.user("Implement runtime adapters and show me the resulting logs.")

    cloud_plan = runtime.cloud.complete(
        "Generate the best next action for runtime-integrated shadow logging.",
        message_type="reasoning",
        metadata={"stage": "planning"},
    )
    codex_reply = runtime.codex.respond(
        cloud_plan,
        message_type="execution",
        metadata={"stage": "execution"},
    )

    runtime.codex.tool(
        "apply_patch",
        arguments={"target": "src/lume/execution/runtime.py"},
        output_summary="Created runtime adapters for invisible logging.",
        metadata={"stage": "execution"},
    )
    runtime.codex.file(
        "src/lume/execution/runtime.py",
        change_type="created",
        summary="Added observed runtime wrappers for cloud and Codex flows.",
        metadata={"stage": "execution"},
    )
    runtime.codex.file(
        "scripts/run_shadow_runtime_demo.py",
        change_type="created",
        summary="Added demo entrypoint for invisible shadow logging.",
        metadata={"stage": "execution"},
    )

    task_dir = runtime.finish(
        result_status="completed",
        value_score=0.99,
        notes=(
            "No-touch runtime demo completed. "
            f"Latest Codex reply: {codex_reply}"
        ),
    )
    print(task_dir)


if __name__ == "__main__":
    main()
