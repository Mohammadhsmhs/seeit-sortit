"""NVIDIA NIM provider — calls NIM endpoints with NVIDIA-specific conventions."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.models.base import LLMProvider
from src.models.parser import parse_category
from src.prompts import load_prompt

logger = logging.getLogger(__name__)


class NIMProvider(LLMProvider):
    """Targets NVIDIA NIM (hosted or on-prem DGX).

    NIM exposes an OpenAI-compatible chat/completions endpoint but uses
    NVIDIA-specific model names and may need extra headers for org routing.
    """

    def __init__(
        self,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model_name: str = "meta/llama-3.1-8b-instruct",
        api_key: str = "",
        embed_model: str = "nvidia/nv-embedqa-e5-v5",
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.embed_model = embed_model
        self.api_key = api_key
        self.timeout = timeout

    # -- helpers -------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        # NIM-specific: some on-prem deployments use this header
        h["NVIDIA-API-PARTNER"] = "london-civic-agent"
        return h

    def _chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.7,  # NIM recommended default
        }
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    # -- interface -----------------------------------------------------------

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._chat(messages)

    def classify(self, text: str, categories: list[str]) -> str:
        prompt_tpl = load_prompt("intake_classify")
        prompt = prompt_tpl.format(description=text)
        system = (
            "You are a classification engine. Reply with ONLY the category name, "
            "nothing else. No explanation, no numbering, no quotes."
        )
        raw = self._chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=64,
        )
        logger.debug("Raw classify response: %r", raw)
        return parse_category(raw)

    def embed(self, text: str) -> list[float]:
        payload = {
            "model": self.embed_model,
            "input": [text],
            "input_type": "query",
            "encoding_format": "float",
            "truncate": "END",
        }
        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
