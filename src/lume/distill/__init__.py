"""Distillation module for dataset building and adapter training."""

from .code_execution import build_real_code_execution_dataset
from .dataset import build_distill_datasets
from .historical_backfill import build_historical_workspace_dataset
from .raw_dialogue import build_raw_dialogue_dataset
from .synthetic import merge_synthetic_corpus
from .train import TrainingConfig, train_local_model

__all__ = [
    "TrainingConfig",
    "build_real_code_execution_dataset",
    "build_distill_datasets",
    "build_historical_workspace_dataset",
    "build_raw_dialogue_dataset",
    "merge_synthetic_corpus",
    "train_local_model",
]
