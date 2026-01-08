"""
OpenRouter LLM client implementation.

OpenRouter provides access to many models through a unified API.
Free tier models available: mistralai/mistral-7b-instruct:free, etc.
"""

import os
import time
from typing import Optional

import httpx

from .base import LLMClient, LLMResponse


class OpenRouterClient(LLMClient):
    """OpenRouter API client."""
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Some free models on OpenRouter (check for current availability)
    FREE_MODELS = [
        "mistralai/mistral-7b-instruct:free",
        "huggingfaceh4/zephyr-7b-beta:free",
        "openchat/openchat-7b:free",
        "nousresearch/nous-capybara-7b:free",
    ]
    
    def __init__(
        self,
        model: str = "mistralai/mistral-7b-instruct:free",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize OpenRouter client.
        
        Args:
            model: Model identifier on OpenRouter
            api_key: OpenRouter API key (or use OPENROUTER_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var or pass api_key."
            )
    
    def get_provider_name(self) -> str:
        return "openrouter"
    
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
        """Generate completion via OpenRouter API."""
        
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
        
        # Enable JSON mode if requested
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/MyLLMTradingAgents",
            "X-Title": "MyLLMTradingAgents",
        }
        
        start_time = time.time()
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers,
                )
                
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code != 200:
                return LLMResponse(
                    content="",
                    latency_ms=latency_ms,
                    model=self.model,
                    error=f"HTTP {response.status_code}: {response.text}",
                )
            
            data = response.json()
            
            # Extract content
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                elif "text" in choice:
                    content = choice["text"]
            
            # Extract usage
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
            latency_ms = int((time.time() - start_time) * 1000)
            return LLMResponse(
                content="",
                latency_ms=latency_ms,
                model=self.model,
                error=str(e),
            )
