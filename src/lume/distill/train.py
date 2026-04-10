"""Training utilities for the Lume prototype.

This module supports two training paths:
1. A real ``transformers + PEFT/LoRA`` causal-LM fine-tuning flow.
2. A small fallback GRU trainer when the transformer path is unavailable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

try:
    from peft import LoraConfig, PeftModel, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup

    _TRANSFORMERS_AVAILABLE = True
except Exception:
    LoraConfig = None
    PeftModel = None
    TaskType = None
    get_peft_model = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    get_linear_schedule_with_warmup = None
    _TRANSFORMERS_AVAILABLE = False


SPECIAL_TOKENS = ["<pad>", "<bos>", "<eos>"]
DEFAULT_DATASET_FILES = [
    "raw_dialogue_sft.jsonl",
    "real_cloud_dialogue_sft.jsonl",
    "real_cloud_bootstrap_sft.jsonl",
    "real_cloud_full_fidelity_sft.jsonl",
    "real_code_execution_sft.jsonl",
    "battery_cascade_sft.jsonl",
    "hybrid_refinement_sft.jsonl",
    "historical_workspace_code_sft.jsonl",
    "sft_reasoning.jsonl",
    "sft_execution.jsonl",
    "memory_update.jsonl",
    "synthetic_sft.jsonl",
]


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


def load_training_records(datasets_root: Path) -> list[dict[str, Any]]:
    """Load all available SFT-style datasets into normalized input/target records."""
    normalized: list[dict[str, Any]] = []
    for filename in DEFAULT_DATASET_FILES:
        for record in _read_jsonl(datasets_root / filename):
            input_text = str(record.get("input", "")).strip()
            target_value = record.get("target", "")
            target_text = (
                json.dumps(target_value, ensure_ascii=False)
                if isinstance(target_value, (dict, list))
                else str(target_value)
            ).strip()
            if not input_text or not target_text:
                continue
            metadata = record.get("metadata", {})
            normalized.append(
                {
                    "input": input_text,
                    "target": target_text,
                    "metadata": metadata if isinstance(metadata, dict) else {},
                }
            )
    return normalized


def format_supervised_example(input_text: str, target_text: str) -> tuple[str, str]:
    prompt = f"User:\n{input_text}\n\nAssistant:\n"
    completion = target_text
    return prompt, completion


def load_training_texts(datasets_root: Path) -> list[str]:
    """Load all available SFT-style datasets into prompt/target texts."""
    texts: list[str] = []
    for record in load_training_records(datasets_root):
        prompt, completion = format_supervised_example(record["input"], record["target"])
        texts.append(f"{prompt}{completion}")
    return texts


def build_vocab(texts: list[str]) -> dict[str, int]:
    chars = sorted({char for text in texts for char in text})
    vocab = {token: index for index, token in enumerate(SPECIAL_TOKENS)}
    for char in chars:
        if char not in vocab:
            vocab[char] = len(vocab)
    return vocab


def encode_text(text: str, vocab: dict[str, int]) -> list[int]:
    bos_id = vocab["<bos>"]
    eos_id = vocab["<eos>"]
    return [bos_id] + [vocab[char] for char in text if char in vocab] + [eos_id]


class TextSequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Fixed-length next-token prediction dataset for fallback training."""

    def __init__(self, texts: list[str], vocab: dict[str, int], block_size: int) -> None:
        self.pad_id = vocab["<pad>"]
        self.samples: list[tuple[torch.Tensor, torch.Tensor]] = []
        for text in texts:
            token_ids = encode_text(text, vocab)
            token_ids = token_ids[: block_size + 1]
            if len(token_ids) < 2:
                continue
            x_ids = token_ids[:-1]
            y_ids = token_ids[1:]
            while len(x_ids) < block_size:
                x_ids.append(self.pad_id)
                y_ids.append(self.pad_id)
            self.samples.append(
                (
                    torch.tensor(x_ids, dtype=torch.long),
                    torch.tensor(y_ids, dtype=torch.long),
                )
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.samples[index]


class TinyCausalLM(nn.Module):
    """Small GRU-based character LM that can train quickly on CPU."""

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.rnn = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.head = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(x)
        output, _ = self.rnn(embedded)
        return self.head(output)


class SupervisedCausalDataset(Dataset[dict[str, torch.Tensor]]):
    """Supervised causal LM dataset with prompt loss masking."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: Any,
        *,
        max_length: int,
    ) -> None:
        self.samples: list[dict[str, torch.Tensor]] = []
        for record in records:
            prompt, completion = format_supervised_example(record["input"], record["target"])
            prompt_ids = tokenizer(
                prompt,
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            full_ids = tokenizer(
                f"{prompt}{completion}",
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            if len(full_ids) <= len(prompt_ids):
                continue
            attention_mask = [1] * len(full_ids)
            labels = full_ids.copy()
            for index in range(min(len(prompt_ids), len(labels))):
                labels[index] = -100
            self.samples.append(
                {
                    "input_ids": torch.tensor(full_ids, dtype=torch.long),
                    "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
                    "labels": torch.tensor(labels, dtype=torch.long),
                }
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return self.samples[index]


@dataclass(slots=True)
class TrainingConfig:
    datasets_root: str
    output_root: str
    epochs: int = 3
    batch_size: int = 8
    block_size: int = 256
    embed_dim: int = 96
    hidden_dim: int = 192
    learning_rate: float = 0.003
    seed: int = 42
    max_samples: int | None = None
    training_mode: str = "auto"
    device: str = "auto"
    model_name_or_path: str = "sshleifer/tiny-gpt2"
    max_length: int = 256
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    gradient_accumulation_steps: int = 1
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0


def _resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


def _sample_text(
    model: TinyCausalLM,
    vocab: dict[str, int],
    prompt: str,
    *,
    max_new_tokens: int = 120,
    device: str = "cpu",
) -> str:
    inverse_vocab = {index: token for token, index in vocab.items()}
    model.eval()
    token_ids = encode_text(prompt, vocab)
    device_obj = torch.device(device)
    x = torch.tensor([token_ids], dtype=torch.long, device=device_obj)
    for _ in range(max_new_tokens):
        with torch.no_grad():
            logits = model(x)
        next_id = int(torch.argmax(logits[0, -1]).item())
        if inverse_vocab.get(next_id) == "<eos>":
            break
        x = torch.cat(
            [x, torch.tensor([[next_id]], dtype=torch.long, device=device_obj)],
            dim=1,
        )
    generated = "".join(
        inverse_vocab.get(int(token_id), "")
        for token_id in x[0].tolist()
        if inverse_vocab.get(int(token_id), "") not in SPECIAL_TOKENS
    )
    return generated


def _collect_linear_suffixes(model: Any) -> list[str]:
    suffixes: set[str] = set()
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            suffix = name.rsplit(".", 1)[-1]
            if suffix != "lm_head":
                suffixes.add(suffix)
    return sorted(suffixes)


def _infer_lora_target_modules(model: Any) -> tuple[list[str], bool]:
    preferred_sets = [
        ["q_proj", "k_proj", "v_proj", "o_proj"],
        ["query_key_value"],
        ["Wqkv"],
        ["c_attn", "c_proj", "c_fc"],
    ]
    module_names = [name for name, _module in model.named_modules()]
    for candidate_set in preferred_sets:
        matched = [name for name in candidate_set if any(module.endswith(name) for module in module_names)]
        if matched:
            fan_in_fan_out = any(name.startswith("c_") for name in matched)
            return sorted(set(matched)), fan_in_fan_out
    linear_suffixes = _collect_linear_suffixes(model)
    return linear_suffixes, False


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")


def _load_pretrained_with_local_fallback(loader: Any, model_id_or_path: Any, **kwargs: Any) -> Any:
    """Prefer local cached artifacts to avoid noisy network probes in offline environments."""
    try:
        return loader.from_pretrained(model_id_or_path, local_files_only=True, **kwargs)
    except Exception:
        return loader.from_pretrained(model_id_or_path, **kwargs)


def _train_tiny_fallback(config: TrainingConfig) -> Path:
    datasets_root = Path(config.datasets_root)
    output_root = Path(config.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    texts = load_training_texts(datasets_root)
    if config.max_samples is not None:
        texts = texts[: config.max_samples]
    if not texts:
        raise RuntimeError("No training texts found in datasets root.")

    vocab = build_vocab(texts)
    dataset = TextSequenceDataset(texts, vocab, config.block_size)
    if len(dataset) == 0:
        raise RuntimeError("No valid tokenized samples were produced.")

    device = _resolve_device(config.device)
    device_obj = torch.device(device)
    dataloader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)
    model = TinyCausalLM(
        vocab_size=len(vocab),
        embed_dim=config.embed_dim,
        hidden_dim=config.hidden_dim,
    ).to(device_obj)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss(ignore_index=vocab["<pad>"])

    model.train()
    epoch_losses: list[float] = []
    for _epoch in range(config.epochs):
        running_loss = 0.0
        batches = 0
        for x, y in dataloader:
            x = x.to(device_obj)
            y = y.to(device_obj)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item())
            batches += 1
        epoch_losses.append(running_loss / max(batches, 1))

    final_loss = epoch_losses[-1]
    perplexity = math.exp(final_loss) if final_loss < 20 else float("inf")

    torch.save(model.state_dict(), output_root / "model.pt")
    _save_json(output_root / "vocab.json", vocab)
    config_payload = asdict(config) | {"training_mode": "tiny_lm_fallback"}
    _save_json(output_root / "training_config.json", config_payload)
    metrics = {
        "sample_count": len(dataset),
        "text_count": len(texts),
        "vocab_size": len(vocab),
        "epoch_losses": epoch_losses,
        "final_loss": final_loss,
        "perplexity": perplexity,
        "training_mode": "tiny_lm_fallback",
        "device": str(device_obj),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    _save_json(output_root / "metrics.json", metrics)

    sample_prompt = "User:\n写一篇爱国散文诗\n\nAssistant:\n"
    sample_output = _sample_text(model, vocab, sample_prompt, device=str(device_obj))
    (output_root / "sample_generation.txt").write_text(sample_output + "\n", "utf-8")
    return output_root


def _collate_supervised_batch(samples: list[dict[str, torch.Tensor]], pad_token_id: int) -> dict[str, torch.Tensor]:
    max_len = max(sample["input_ids"].size(0) for sample in samples)
    input_ids: list[torch.Tensor] = []
    attention_masks: list[torch.Tensor] = []
    labels: list[torch.Tensor] = []
    for sample in samples:
        seq_len = sample["input_ids"].size(0)
        pad_len = max_len - seq_len
        if pad_len > 0:
            input_pad = torch.full((pad_len,), pad_token_id, dtype=torch.long)
            mask_pad = torch.zeros((pad_len,), dtype=torch.long)
            label_pad = torch.full((pad_len,), -100, dtype=torch.long)
            input_ids.append(torch.cat([sample["input_ids"], input_pad], dim=0))
            attention_masks.append(torch.cat([sample["attention_mask"], mask_pad], dim=0))
            labels.append(torch.cat([sample["labels"], label_pad], dim=0))
        else:
            input_ids.append(sample["input_ids"])
            attention_masks.append(sample["attention_mask"])
            labels.append(sample["labels"])
    return {
        "input_ids": torch.stack(input_ids, dim=0),
        "attention_mask": torch.stack(attention_masks, dim=0),
        "labels": torch.stack(labels, dim=0),
    }


def _train_transformers_lora(config: TrainingConfig) -> Path:
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError("transformers/peft are not available in the current environment.")

    datasets_root = Path(config.datasets_root)
    output_root = Path(config.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    records = load_training_records(datasets_root)
    if config.max_samples is not None:
        records = records[: config.max_samples]
    if not records:
        raise RuntimeError("No training records found in datasets root.")

    device = _resolve_device(config.device)
    device_obj = torch.device(device)

    tokenizer = _load_pretrained_with_local_fallback(AutoTokenizer, config.model_name_or_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    base_model = _load_pretrained_with_local_fallback(AutoModelForCausalLM, config.model_name_or_path)
    if getattr(base_model.config, "pad_token_id", None) is None and tokenizer.pad_token_id is not None:
        base_model.config.pad_token_id = tokenizer.pad_token_id

    target_modules, fan_in_fan_out = _infer_lora_target_modules(base_model)
    if not target_modules:
        raise RuntimeError("Unable to infer LoRA target modules for the selected base model.")

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=target_modules,
        bias="none",
        fan_in_fan_out=fan_in_fan_out,
    )
    model = get_peft_model(base_model, lora_config)
    model.to(device_obj)
    model.train()

    dataset = SupervisedCausalDataset(records, tokenizer, max_length=config.max_length)
    if len(dataset) == 0:
        raise RuntimeError("No valid supervised transformer samples were produced.")

    dataloader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        collate_fn=lambda samples: _collate_supervised_batch(samples, tokenizer.pad_token_id),
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    total_steps = max(1, math.ceil(len(dataloader) * config.epochs / max(config.gradient_accumulation_steps, 1)))
    warmup_steps = int(total_steps * config.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    epoch_losses: list[float] = []
    optimizer.zero_grad()
    global_step = 0
    for _epoch in range(config.epochs):
        running_loss = 0.0
        batches = 0
        for step, batch in enumerate(dataloader, start=1):
            batch = {key: value.to(device_obj) for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / max(config.gradient_accumulation_steps, 1)
            loss.backward()
            running_loss += float(outputs.loss.item())
            batches += 1
            if step % max(config.gradient_accumulation_steps, 1) == 0 or step == len(dataloader):
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1
        epoch_losses.append(running_loss / max(batches, 1))

    final_loss = epoch_losses[-1]
    perplexity = math.exp(final_loss) if final_loss < 20 else float("inf")

    adapter_root = output_root / "adapter"
    tokenizer_root = output_root / "tokenizer"
    adapter_root.mkdir(parents=True, exist_ok=True)
    tokenizer_root.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_root)
    tokenizer.save_pretrained(tokenizer_root)

    training_config = asdict(config) | {
        "training_mode": "transformers_peft_lora",
        "base_model_name_or_path": config.model_name_or_path,
        "target_modules": target_modules,
        "fan_in_fan_out": fan_in_fan_out,
    }
    _save_json(output_root / "training_config.json", training_config)
    metrics = {
        "sample_count": len(dataset),
        "record_count": len(records),
        "epoch_losses": epoch_losses,
        "final_loss": final_loss,
        "perplexity": perplexity,
        "training_mode": "transformers_peft_lora",
        "device": str(device_obj),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "base_model_name_or_path": config.model_name_or_path,
        "target_modules": target_modules,
        "fan_in_fan_out": fan_in_fan_out,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "global_steps": global_step,
    }
    _save_json(output_root / "metrics.json", metrics)

    model.eval()
    sample_prompt = "User:\n写一篇爱国散文诗\n\nAssistant:\n"
    sample_inputs = tokenizer(sample_prompt, return_tensors="pt").to(device_obj)
    with torch.no_grad():
        generated_ids = model.generate(
            **sample_inputs,
            max_new_tokens=120,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    sample_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    (output_root / "sample_generation.txt").write_text(sample_output + "\n", "utf-8")
    return output_root


def train_local_model(config: TrainingConfig) -> Path:
    """Train a local model and save artifacts."""
    random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)

    mode = config.training_mode
    if mode == "auto":
        mode = "transformers_peft_lora" if _TRANSFORMERS_AVAILABLE else "tiny_lm_fallback"

    if mode == "transformers_peft_lora":
        return _train_transformers_lora(config)
    if mode == "tiny_lm_fallback":
        return _train_tiny_fallback(config)
    raise ValueError(f"Unsupported training mode: {config.training_mode}")


def load_peft_model(model_root: Path, *, device: str = "auto") -> tuple[Any, Any, dict[str, Any]]:
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError("transformers/peft are not available in the current environment.")
    config = json.loads((model_root / "training_config.json").read_text("utf-8"))
    base_model_name = config["base_model_name_or_path"]
    tokenizer = _load_pretrained_with_local_fallback(AutoTokenizer, model_root / "tokenizer")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = _load_pretrained_with_local_fallback(AutoModelForCausalLM, base_model_name)
    try:
        model = PeftModel.from_pretrained(base_model, model_root / "adapter", local_files_only=True)
    except Exception:
        model = PeftModel.from_pretrained(base_model, model_root / "adapter")
    device_obj = torch.device(_resolve_device(device))
    model.to(device_obj)
    model.eval()
    return model, tokenizer, config
