from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, system_prompt: str | None = None, history: list[dict[str, str]] | None = None) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, *, system_prompt: str | None = None, history: list[dict[str, str]] | None = None) -> str:
        if not self.api_key:
            return "AI provider is not configured. Set OPENAI_API_KEY or provide an OpenAI-compatible endpoint."

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, *, system_prompt: str | None = None, history: list[dict[str, str]] | None = None) -> str:
        if not self.api_key:
            return "AI provider is not configured. Set AI_API_KEY to your Gemini API key."

        contents: list[dict[str, Any]] = []
        if history:
            for message in history:
                role = "model" if message.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": message.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: dict[str, Any] = {"contents": contents}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        url = f"{self.base_url}/models/{self.model}:generateContent"
        response = requests.post(
            url,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        try:
            candidates = data["candidates"]
            if not candidates:
                raise KeyError("no candidates returned")
            parts = candidates[0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts).strip() or "Gemini returned an empty response."
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected Gemini response format: {data}") from exc
