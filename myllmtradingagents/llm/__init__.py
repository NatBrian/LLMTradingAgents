"""LLM client implementations for MyLLMTradingAgents."""

from .base import LLMClient, LLMResponse
from .openrouter import OpenRouterClient
from .gemini import GeminiClient
from .openai_compatible import OpenAICompatibleClient
from .prompts import build_repair_prompt

__all__ = [
    # LLM Clients
    "LLMClient",
    "LLMResponse",
    "OpenRouterClient",
    "GeminiClient",
    "OpenAICompatibleClient",
    "create_llm_client",
    # Prompts
    "build_repair_prompt",
]


def create_llm_client(provider: str, model: str, api_key: str = "", base_url: str = "") -> LLMClient:
    """Factory function to create LLM client by provider name."""
    provider = provider.lower()
    
    if provider == "openrouter":
        return OpenRouterClient(model=model, api_key=api_key)
    elif provider == "gemini":
        return GeminiClient(model=model, api_key=api_key)
    elif provider in {"openai", "openai_compatible", "custom_openai", "custom-openai"}:
        return OpenAICompatibleClient(model=model, api_key=api_key, base_url=base_url)
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. Supported: openrouter, gemini, openai_compatible"
        )
