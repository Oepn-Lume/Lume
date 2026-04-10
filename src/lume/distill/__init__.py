"""Distillation module for dataset building and adapter training."""

from .battery_cascade import build_battery_cascade_dataset
from .battery_state_density import build_battery_state_dataset
from .code_execution import build_real_code_execution_dataset
from .codex_actions import build_continue_state_sft_dataset, build_continue_task_contexts
from .dataset import build_distill_datasets
from .historical_backfill import build_historical_workspace_dataset
from .hybrid_refinement import build_hybrid_refinement_dataset
from .onsite_alignment import build_onsite_alignment_datasets
from .raw_dialogue import build_raw_dialogue_dataset
from .synthetic import merge_synthetic_corpus
from .train import (
    DEFAULT_STAGE_ONE_DATASET_FILES,
    DEFAULT_STAGE_TWO_DATASET_FILES,
    TrainingConfig,
    TwoStageTrainingResult,
    normalize_dataset_files,
    train_local_model,
    train_two_stage_local_model,
)

__all__ = [
    "TrainingConfig",
    "TwoStageTrainingResult",
    "DEFAULT_STAGE_ONE_DATASET_FILES",
    "DEFAULT_STAGE_TWO_DATASET_FILES",
    "build_battery_cascade_dataset",
    "build_battery_state_dataset",
    "build_continue_state_sft_dataset",
    "build_continue_task_contexts",
    "build_real_code_execution_dataset",
    "build_distill_datasets",
    "build_historical_workspace_dataset",
    "build_hybrid_refinement_dataset",
    "build_onsite_alignment_datasets",
    "build_raw_dialogue_dataset",
    "normalize_dataset_files",
    "merge_synthetic_corpus",
    "train_local_model",
    "train_two_stage_local_model",
]
