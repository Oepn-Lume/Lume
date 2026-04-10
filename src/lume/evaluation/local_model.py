"""Inference and evaluation helpers for locally trained models."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import torch
from torch import nn

from lume.distill.train import (
    SPECIAL_TOKENS,
    TinyCausalLM,
    encode_text,
    format_supervised_example,
    load_peft_model,
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def _safe_tokenizer_max_length(tokenizer: Any, config: dict[str, Any] | None = None) -> int:
    configured = int((config or {}).get("max_length", 0) or 0)
    tokenizer_limit = int(getattr(tokenizer, "model_max_length", 0) or 0)
    candidates = [value for value in (configured, tokenizer_limit) if 0 < value < 100_000]
    return min(candidates) if candidates else 512


def _resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


def _training_mode(model_root: Path) -> str:
    config_path = model_root / "training_config.json"
    if not config_path.exists():
        return "tiny_lm_fallback"
    config = _read_json(config_path)
    return str(config.get("training_mode", "tiny_lm_fallback"))


def load_trained_model(model_root: Path) -> tuple[TinyCausalLM, dict[str, int], dict[str, Any]]:
    """Load a previously trained tiny fallback model."""
    config = _read_json(model_root / "training_config.json")
    vocab = _read_json(model_root / "vocab.json")
    model = TinyCausalLM(
        vocab_size=len(vocab),
        embed_dim=int(config["embed_dim"]),
        hidden_dim=int(config["hidden_dim"]),
    )
    state_dict = torch.load(model_root / "model.pt", map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()
    return model, vocab, config


def generate_text(
    model_root: Path,
    prompt: str,
    *,
    max_new_tokens: int = 160,
    device: str = "auto",
) -> str:
    """Generate text from the trained local model."""
    mode = _training_mode(model_root)
    if mode.startswith("transformers_peft_"):
        model, tokenizer, config = load_peft_model(model_root, device=device)
        device_obj = torch.device(_resolve_device(device))
        return _generate_with_loaded_peft_model(
            model,
            tokenizer,
            prompt,
            max_new_tokens=max_new_tokens,
            device_obj=device_obj,
            config=config,
        )

    model, vocab, _config = load_trained_model(model_root)
    inverse_vocab = {index: token for token, index in vocab.items()}
    device_obj = torch.device(_resolve_device(device))
    model.to(device_obj)
    token_ids = encode_text(prompt, vocab)
    x = torch.tensor([token_ids], dtype=torch.long, device=device_obj)
    for _ in range(max_new_tokens):
        with torch.no_grad():
            logits = model(x)
        next_id = int(torch.argmax(logits[0, -1]).item())
        token = inverse_vocab.get(next_id, "")
        if token == "<eos>":
            break
        x = torch.cat([x, torch.tensor([[next_id]], dtype=torch.long, device=device_obj)], dim=1)
    return "".join(
        inverse_vocab.get(int(token_id), "")
        for token_id in x[0].tolist()
        if inverse_vocab.get(int(token_id), "") not in SPECIAL_TOKENS
    )


def _generate_with_loaded_peft_model(
    model: Any,
    tokenizer: Any,
    prompt: str,
    *,
    max_new_tokens: int,
    device_obj: torch.device,
    config: dict[str, Any] | None = None,
) -> str:
    max_length = _safe_tokenizer_max_length(tokenizer, config)
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    ).to(device_obj)
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    prompt_length = int(inputs["input_ids"].shape[1])
    new_token_ids = generated_ids[0][prompt_length:]
    return tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()


def evaluate_model(
    model_root: Path,
    dataset_path: Path,
    *,
    max_examples: int = 32,
    device: str = "auto",
) -> dict[str, Any]:
    """Evaluate the local model on simple LM loss and output similarity."""
    mode = _training_mode(model_root)
    lines = [line for line in dataset_path.read_text("utf-8", errors="ignore").splitlines() if line.strip()]
    examples = [json.loads(line) for line in lines[:max_examples]]
    device_obj = torch.device(_resolve_device(device))

    losses: list[float] = []
    char_match_scores: list[float] = []
    exact_prefix_matches = 0

    if mode.startswith("transformers_peft_"):
        model, tokenizer, config = load_peft_model(model_root, device=device)
        model.eval()
        max_length = int(config.get("max_length", getattr(tokenizer, "model_max_length", 512)))
        for example in examples:
            input_text = str(example.get("input", "")).strip()
            target_value = example.get("target", "")
            target_text = (
                json.dumps(target_value, ensure_ascii=False)
                if isinstance(target_value, (dict, list))
                else str(target_value)
            ).strip()
            if not input_text or not target_text:
                continue

            prompt, completion = format_supervised_example(input_text, target_text)
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
            labels = full_ids.copy()
            for index in range(min(len(prompt_ids), len(labels))):
                labels[index] = -100
            input_tensor = torch.tensor([full_ids], dtype=torch.long, device=device_obj)
            attention_tensor = torch.ones_like(input_tensor, device=device_obj)
            label_tensor = torch.tensor([labels], dtype=torch.long, device=device_obj)
            with torch.no_grad():
                outputs = model(
                    input_ids=input_tensor,
                    attention_mask=attention_tensor,
                    labels=label_tensor,
                )
            losses.append(float(outputs.loss.item()))

            generated = _generate_with_loaded_peft_model(
                model,
                tokenizer,
                prompt,
                max_new_tokens=min(160, max(32, len(target_text))),
                device_obj=device_obj,
                config=config,
            )
            generated_tail = generated.split("Assistant:\n", 1)[-1]
            compare_len = max(1, min(len(generated_tail), len(target_text)))
            match_count = sum(
                1 for index in range(compare_len)
                if generated_tail[index:index + 1] == target_text[index:index + 1]
            )
            char_match_scores.append(match_count / compare_len)
            if target_text and generated_tail.startswith(target_text[: min(12, len(target_text))]):
                exact_prefix_matches += 1
    else:
        model, vocab, _config = load_trained_model(model_root)
        pad_id = vocab["<pad>"]
        criterion = nn.CrossEntropyLoss(ignore_index=pad_id)
        model.to(device_obj)
        for example in examples:
            input_text = str(example.get("input", "")).strip()
            target_value = example.get("target", "")
            target_text = (
                json.dumps(target_value, ensure_ascii=False)
                if isinstance(target_value, (dict, list))
                else str(target_value)
            ).strip()
            if not input_text or not target_text:
                continue

            train_text = f"User:\n{input_text}\n\nAssistant:\n{target_text}"
            token_ids = encode_text(train_text, vocab)
            if len(token_ids) < 2:
                continue
            x = torch.tensor([token_ids[:-1]], dtype=torch.long, device=device_obj)
            y = torch.tensor([token_ids[1:]], dtype=torch.long, device=device_obj)
            with torch.no_grad():
                logits = model(x)
                loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
            losses.append(float(loss.item()))

            prompt = f"User:\n{input_text}\n\nAssistant:\n"
            generated = generate_text(
                model_root,
                prompt,
                max_new_tokens=min(160, max(32, len(target_text))),
                device=device,
            )
            generated_tail = generated.split("Assistant:\n", 1)[-1]
            compare_len = max(1, min(len(generated_tail), len(target_text)))
            match_count = sum(
                1 for index in range(compare_len)
                if generated_tail[index:index + 1] == target_text[index:index + 1]
            )
            char_match_scores.append(match_count / compare_len)
            if target_text and generated_tail.startswith(target_text[: min(12, len(target_text))]):
                exact_prefix_matches += 1

    avg_loss = sum(losses) / len(losses) if losses else None
    perplexity = math.exp(avg_loss) if avg_loss is not None and avg_loss < 20 else None
    avg_char_match = sum(char_match_scores) / len(char_match_scores) if char_match_scores else 0.0
    return {
        "examples_evaluated": len(losses),
        "avg_loss": avg_loss,
        "perplexity": perplexity,
        "avg_char_match": avg_char_match,
        "exact_prefix_match_rate": exact_prefix_matches / len(losses) if losses else 0.0,
        "dataset_path": str(dataset_path),
        "device": str(device_obj),
        "training_mode": mode,
    }
