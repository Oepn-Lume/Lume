"""Ollama-backed local Battery Model handler."""

from __future__ import annotations

import json
from urllib import error, request


class OllamaLocalHandler:
    """Minimal Ollama client for local Battery Model completions."""

    def __init__(
        self,
        *,
        model: str = "gemma4:31b",
        endpoint: str = "http://127.0.0.1:11434/api/generate",
        tags_endpoint: str = "http://127.0.0.1:11434/api/tags",
        timeout: int = 120,
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.tags_endpoint = tags_endpoint
        self.timeout = timeout
        self.temperature = temperature

    @property
    def available(self) -> bool:
        try:
            http_request = request.Request(self.tags_endpoint, method="GET")
            with request.urlopen(http_request, timeout=min(self.timeout, 10)) as response:
                payload = json.loads(response.read().decode("utf-8"))
            models = payload.get("models", [])
            return any(model.get("name") == self.model for model in models)
        except Exception:  # noqa: BLE001
            return False

    def complete(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama request failed with HTTP {exc.code}: {detail}") from exc
        return str(response_payload.get("response", "")).strip()
