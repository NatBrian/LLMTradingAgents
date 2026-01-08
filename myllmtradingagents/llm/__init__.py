"""LLM client implementations for MyLLMTradingAgents."""

from .base import LLMClient, LLMResponse
from .openrouter import OpenRouterClient
from .gemini import GeminiClient
from .prompts import build_repair_prompt

__all__ = [
    # LLM Clients
    "LLMClient",
    "LLMResponse",
    "OpenRouterClient",
    "GeminiClient",
    "create_llm_client",
    # Prompts
    "build_repair_prompt",
]


def create_llm_client(provider: str, model: str, api_key: str = "") -> LLMClient:
    """Factory function to create LLM client by provider name."""
    provider = provider.lower()
    
    if provider == "openrouter":
        return OpenRouterClient(model=model, api_key=api_key)
    elif provider == "gemini":
        return GeminiClient(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: openrouter, gemini")
