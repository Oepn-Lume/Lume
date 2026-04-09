"""Minimal preference optimization for Lume RLEF datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset

from lume.distill.train import (
    AutoModelForCausalLM,
    AutoTokenizer,
    LoraConfig,
    TaskType,
    _TRANSFORMERS_AVAILABLE,
    _infer_lora_target_modules,
    _load_pretrained_with_local_fallback,
    _resolve_device,
    _save_json,
    get_linear_schedule_with_warmup,
    get_peft_model,
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


@dataclass(slots=True)
class PreferenceTrainingConfig:
    dataset_path: str
    output_root: str
    model_name_or_path: str = "uer/gpt2-chinese-cluecorpussmall"
    epochs: int = 1
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 0.0
    warmup_ratio: float = 0.03
    gradient_accumulation_steps: int = 1
    max_length: int = 256
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    beta: float = 0.1
    max_samples: int | None = None
    seed: int = 42
    device: str = "auto"


class PreferenceDataset(Dataset[dict[str, Any]]):
    """Tokenized prompt/chosen/rejected pairs for preference optimization."""

    def __init__(self, records: list[dict[str, Any]], tokenizer: Any, *, max_length: int) -> None:
        self.samples: list[dict[str, Any]] = []
        for record in records:
            prompt = str(record.get("prompt", "")).strip()
            chosen = str(record.get("chosen", "")).strip()
            rejected = str(record.get("rejected", "")).strip()
            if not prompt or not chosen or not rejected:
                continue

            prompt_ids = tokenizer(
                f"User:\n{prompt}\n\nAssistant:\n",
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            chosen_full = tokenizer(
                f"User:\n{prompt}\n\nAssistant:\n{chosen}",
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            rejected_full = tokenizer(
                f"User:\n{prompt}\n\nAssistant:\n{rejected}",
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            if len(chosen_full) <= len(prompt_ids) or len(rejected_full) <= len(prompt_ids):
                continue

            self.samples.append(
                {
                    "chosen_input_ids": torch.tensor(chosen_full, dtype=torch.long),
                    "chosen_attention_mask": torch.ones(len(chosen_full), dtype=torch.long),
                    "chosen_labels": self._masked_labels(chosen_full, len(prompt_ids)),
                    "rejected_input_ids": torch.tensor(rejected_full, dtype=torch.long),
                    "rejected_attention_mask": torch.ones(len(rejected_full), dtype=torch.long),
                    "rejected_labels": self._masked_labels(rejected_full, len(prompt_ids)),
                }
            )

    @staticmethod
    def _masked_labels(token_ids: list[int], prompt_len: int) -> torch.Tensor:
        labels = token_ids.copy()
        for index in range(min(prompt_len, len(labels))):
            labels[index] = -100
        return torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.samples[index]


def _pad_tensor_list(tensors: list[torch.Tensor], fill_value: int) -> torch.Tensor:
    max_len = max(tensor.size(0) for tensor in tensors)
    padded: list[torch.Tensor] = []
    for tensor in tensors:
        pad_len = max_len - tensor.size(0)
        if pad_len > 0:
            pad = torch.full((pad_len,), fill_value, dtype=tensor.dtype)
            padded.append(torch.cat([tensor, pad], dim=0))
        else:
            padded.append(tensor)
    return torch.stack(padded, dim=0)


def _collate_preference_batch(samples: list[dict[str, Any]], pad_token_id: int) -> dict[str, torch.Tensor]:
    return {
        "chosen_input_ids": _pad_tensor_list([sample["chosen_input_ids"] for sample in samples], pad_token_id),
        "chosen_attention_mask": _pad_tensor_list(
            [sample["chosen_attention_mask"] for sample in samples], 0
        ),
        "chosen_labels": _pad_tensor_list([sample["chosen_labels"] for sample in samples], -100),
        "rejected_input_ids": _pad_tensor_list(
            [sample["rejected_input_ids"] for sample in samples], pad_token_id
        ),
        "rejected_attention_mask": _pad_tensor_list(
            [sample["rejected_attention_mask"] for sample in samples], 0
        ),
        "rejected_labels": _pad_tensor_list([sample["rejected_labels"] for sample in samples], -100),
    }


def _sequence_logprob(model: Any, input_ids: torch.Tensor, attention_mask: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    logits = outputs.logits[:, :-1, :]
    shifted_labels = labels[:, 1:]
    valid_mask = shifted_labels.ne(-100)
    safe_labels = shifted_labels.masked_fill(~valid_mask, 0)
    token_logprobs = torch.log_softmax(logits, dim=-1).gather(-1, safe_labels.unsqueeze(-1)).squeeze(-1)
    token_logprobs = token_logprobs * valid_mask
    lengths = valid_mask.sum(dim=-1).clamp_min(1)
    return token_logprobs.sum(dim=-1) / lengths


def train_preference_model(config: PreferenceTrainingConfig) -> Path:
    """Run a minimal DPO-style LoRA preference optimization stage."""
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError("transformers/peft are not available in the current environment.")

    random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)

    dataset_path = Path(config.dataset_path)
    output_root = Path(config.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = _read_jsonl(dataset_path)
    if config.max_samples is not None:
        records = records[: config.max_samples]
    if not records:
        raise RuntimeError("No preference records found for RLEF training.")

    device = _resolve_device(config.device)
    device_obj = torch.device(device)

    tokenizer = _load_pretrained_with_local_fallback(AutoTokenizer, config.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    policy_base = _load_pretrained_with_local_fallback(AutoModelForCausalLM, config.model_name_or_path)
    reference_model = _load_pretrained_with_local_fallback(AutoModelForCausalLM, config.model_name_or_path)
    if getattr(policy_base.config, "pad_token_id", None) is None and tokenizer.pad_token_id is not None:
        policy_base.config.pad_token_id = tokenizer.pad_token_id
        reference_model.config.pad_token_id = tokenizer.pad_token_id

    target_modules, fan_in_fan_out = _infer_lora_target_modules(policy_base)
    if not target_modules:
        raise RuntimeError("Unable to infer LoRA target modules for preference optimization.")

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=target_modules,
        bias="none",
        fan_in_fan_out=fan_in_fan_out,
    )
    policy_model = get_peft_model(policy_base, lora_config)
    policy_model.to(device_obj)
    policy_model.train()
    reference_model.to(device_obj)
    reference_model.eval()
    for parameter in reference_model.parameters():
        parameter.requires_grad = False

    dataset = PreferenceDataset(records, tokenizer, max_length=config.max_length)
    if len(dataset) == 0:
        raise RuntimeError("No valid preference samples were produced.")

    dataloader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        collate_fn=lambda samples: _collate_preference_batch(samples, tokenizer.pad_token_id),
    )
    optimizer = torch.optim.AdamW(
        policy_model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    total_steps = max(1, math.ceil(len(dataloader) * config.epochs / max(config.gradient_accumulation_steps, 1)))
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * config.warmup_ratio),
        num_training_steps=total_steps,
    )

    epoch_losses: list[float] = []
    preference_margins: list[float] = []
    optimizer.zero_grad()
    global_step = 0
    for _epoch in range(config.epochs):
        running_loss = 0.0
        batches = 0
        for step, batch in enumerate(dataloader, start=1):
            batch = {key: value.to(device_obj) for key, value in batch.items()}
            chosen_policy = _sequence_logprob(
                policy_model,
                batch["chosen_input_ids"],
                batch["chosen_attention_mask"],
                batch["chosen_labels"],
            )
            rejected_policy = _sequence_logprob(
                policy_model,
                batch["rejected_input_ids"],
                batch["rejected_attention_mask"],
                batch["rejected_labels"],
            )
            with torch.no_grad():
                chosen_reference = _sequence_logprob(
                    reference_model,
                    batch["chosen_input_ids"],
                    batch["chosen_attention_mask"],
                    batch["chosen_labels"],
                )
                rejected_reference = _sequence_logprob(
                    reference_model,
                    batch["rejected_input_ids"],
                    batch["rejected_attention_mask"],
                    batch["rejected_labels"],
                )

            preference_logits = config.beta * (
                (chosen_policy - rejected_policy) - (chosen_reference - rejected_reference)
            )
            loss = -torch.nn.functional.logsigmoid(preference_logits).mean()
            (loss / max(config.gradient_accumulation_steps, 1)).backward()

            running_loss += float(loss.item())
            batches += 1
            preference_margins.extend((chosen_policy - rejected_policy).detach().cpu().tolist())

            if step % max(config.gradient_accumulation_steps, 1) == 0 or step == len(dataloader):
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1
        epoch_losses.append(running_loss / max(batches, 1))

    adapter_root = output_root / "adapter"
    tokenizer_root = output_root / "tokenizer"
    adapter_root.mkdir(parents=True, exist_ok=True)
    tokenizer_root.mkdir(parents=True, exist_ok=True)
    policy_model.save_pretrained(adapter_root)
    tokenizer.save_pretrained(tokenizer_root)

    training_config = asdict(config) | {
        "training_mode": "transformers_peft_dpo",
        "base_model_name_or_path": config.model_name_or_path,
        "target_modules": target_modules,
        "fan_in_fan_out": fan_in_fan_out,
        "dataset_record_count": len(records),
        "sample_count": len(dataset),
    }
    _save_json(output_root / "training_config.json", training_config)
    _save_json(
        output_root / "metrics.json",
        {
            "sample_count": len(dataset),
            "record_count": len(records),
            "epoch_losses": epoch_losses,
            "final_loss": epoch_losses[-1],
            "training_mode": "transformers_peft_dpo",
            "device": str(device_obj),
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "base_model_name_or_path": config.model_name_or_path,
            "target_modules": target_modules,
            "fan_in_fan_out": fan_in_fan_out,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "global_steps": global_step,
            "beta": config.beta,
            "avg_preference_margin": (
                sum(preference_margins) / len(preference_margins) if preference_margins else None
            ),
        },
    )
    return output_root


def evaluate_preference_model(
    model_root: Path,
    dataset_path: Path,
    *,
    max_examples: int = 32,
    device: str = "auto",
) -> dict[str, Any]:
    """Measure how often the policy prefers the chosen response over the rejected one."""
    from lume.distill.train import load_peft_model

    records = _read_jsonl(dataset_path)[:max_examples]
    if not records:
        return {
            "examples_evaluated": 0,
            "chosen_win_rate": None,
            "avg_margin": None,
            "dataset_path": str(dataset_path),
        }

    model, tokenizer, _config = load_peft_model(model_root, device=device)
    device_obj = torch.device(_resolve_device(device))
    dataset = PreferenceDataset(records, tokenizer, max_length=int(_config.get("max_length", 256)))
    if len(dataset) == 0:
        return {
            "examples_evaluated": 0,
            "chosen_win_rate": None,
            "avg_margin": None,
            "dataset_path": str(dataset_path),
        }

    dataloader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        collate_fn=lambda samples: _collate_preference_batch(samples, tokenizer.pad_token_id),
    )
    margins: list[float] = []
    wins = 0
    model.eval()
    for batch in dataloader:
        batch = {key: value.to(device_obj) for key, value in batch.items()}
        with torch.no_grad():
            chosen = _sequence_logprob(
                model,
                batch["chosen_input_ids"],
                batch["chosen_attention_mask"],
                batch["chosen_labels"],
            )
            rejected = _sequence_logprob(
                model,
                batch["rejected_input_ids"],
                batch["rejected_attention_mask"],
                batch["rejected_labels"],
            )
        margin = float((chosen - rejected).item())
        margins.append(margin)
        if margin > 0:
            wins += 1
    return {
        "examples_evaluated": len(margins),
        "chosen_win_rate": wins / len(margins) if margins else None,
        "avg_margin": sum(margins) / len(margins) if margins else None,
        "dataset_path": str(dataset_path),
        "device": str(device_obj),
    }
