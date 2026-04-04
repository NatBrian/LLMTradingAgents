"""
OpenAI-compatible LLM client implementation.

This client targets any API that exposes the OpenAI Chat Completions schema,
including custom routers or reverse proxies with a configurable base URL.
"""

import os
import time
from typing import Optional

import httpx

from .base import LLMClient, LLMResponse
import logging

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(LLMClient):
    """OpenAI-compatible chat completions client."""

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("CUSTOM_OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.getenv("CUSTOM_OPENAI_BASE_URL", "") or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "OpenAI-compatible API key required. Set CUSTOM_OPENAI_API_KEY or OPENAI_API_KEY, or pass api_key."
            )

    def get_provider_name(self) -> str:
        return "openai_compatible"

    def get_model_name(self) -> str:
        return self.model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        logger.debug("Sending OpenAI-compatible request", extra={"model": self.model, "base_url": self.base_url, "json_mode": json_mode})
        start_time = time.time()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)

            latency_ms = int((time.time() - start_time) * 1000)
            if response.status_code != 200:
                return LLMResponse(
                    content="",
                    latency_ms=latency_ms,
                    model=self.model,
                    error=f"HTTP {response.status_code}: {response.text}",
                )

            data = response.json()
            content = ""
            if data.get("choices"):
                choice = data["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "") or choice.get("text", "")

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            return LLMResponse(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                model=self.model,
                raw_response=data,
            )
        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content="",
                latency_ms=latency_ms,
                model=self.model,
                error=f"Request timeout after {self.timeout}s",
            )
        except Exception as e:
            logger.error(f"OpenAI-compatible request failed: {e}", extra={"error": str(e)})
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content="",
                latency_ms=latency_ms,
                model=self.model,
                error=str(e),
            )
