\
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ChatClient(Protocol):
    def complete(self, messages: list[dict], model: str, temperature: float, max_tokens: int) -> str: ...


@dataclass
class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat-completions client using urllib.

    Examples:
      OPENAI_API_KEY=... python -m medesq.generate --provider openai_compatible --base-url https://api.openai.com/v1
      OPENAI_API_KEY=... python -m medesq.generate --provider openai_compatible --base-url https://api.x.ai/v1
    """
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str = "https://api.openai.com/v1"

    def complete(self, messages: list[dict], model: str, temperature: float, max_tokens: int) -> str:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as response:  # noqa: S310 - user-controlled experiment endpoint.
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


@dataclass
class MockGoldClient:
    """Smoke-test client. generate.py injects the gold query into the prompt payload."""
    gold_query: dict | None = None

    def complete(self, messages: list[dict], model: str, temperature: float, max_tokens: int) -> str:  # noqa: ARG002
        return json.dumps({"standard_terms": [], "retrieved_patterns": ["mock_gold"], "es_query": self.gold_query or {}}, ensure_ascii=False)
