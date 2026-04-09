"""OpenAI-backed cloud handler for observed runtime logging."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib import request


class OpenAICloudHandler:
    """Minimal OpenAI Responses API client for cloud planning calls."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gpt-5",
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))

        if "output_text" in response_payload and response_payload["output_text"]:
            return str(response_payload["output_text"])

        # Fallback for payloads where text is nested in output items.
        output_items = response_payload.get("output", [])
        text_chunks: list[str] = []
        for item in output_items:
            for content in item.get("content", []):
                text_value = content.get("text")
                if text_value:
                    text_chunks.append(str(text_value))
        return "\n".join(text_chunks).strip()
