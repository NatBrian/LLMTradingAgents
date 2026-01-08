"""
Abstract base class for LLM clients.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    model: str = ""
    raw_response: Optional[dict] = None
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None


class LLMClient(ABC):
    """Abstract base class for LLM API clients."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system message
            json_mode: If True, request JSON output mode
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            
        Returns:
            LLMResponse with content and metadata
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openrouter', 'gemini')."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass
    
    def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 1,
    ) -> LLMResponse:
        """
        Generate with retry on failure.
        
        Args:
            max_retries: Number of retry attempts on failure
            
        Returns:
            LLMResponse
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            if response.success:
                return response
            
            last_error = response.error
        
        # Return last failed response
        return LLMResponse(
            content="",
            error=f"Failed after {max_retries + 1} attempts. Last error: {last_error}",
        )
