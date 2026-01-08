"""
Google Gemini LLM client implementation.

Uses the google-generativeai library for direct Gemini API access.
Free tier: gemini-1.5-flash with generous limits.
"""

import os
import time
from typing import Optional

from .base import LLMClient, LLMResponse


class GeminiClient(LLMClient):
    """Google Gemini API client."""
    
    # Free tier models
    FREE_MODELS = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.0-pro",
    ]
    
    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
    ):
        """
        Initialize Gemini client.
        
        Args:
            model: Gemini model name
            api_key: Google API key (or use GOOGLE_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY env var or pass api_key."
            )
        
        # Import and configure here to allow graceful failure if not installed
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._model_obj = genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError(
                "google-generativeai package required. Install with: pip install google-generativeai"
            )
    
    def get_provider_name(self) -> str:
        return "gemini"
    
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
        """Generate completion via Gemini API."""
        
        start_time = time.time()
        
        try:
            # Build generation config
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Enable JSON mode if requested
            if json_mode:
                generation_config["response_mime_type"] = "application/json"
            
            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
            
            # Generate response
            response = self._model_obj.generate_content(
                full_prompt,
                generation_config=self._genai.types.GenerationConfig(**generation_config),
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract content
            content = ""
            if response.text:
                content = response.text
            elif response.parts:
                content = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            
            # Extract usage (if available)
            prompt_tokens = 0
            completion_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
            
            return LLMResponse(
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=latency_ms,
                model=self.model,
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Handle specific Gemini errors
            if "SAFETY" in error_msg.upper():
                error_msg = f"Content blocked by safety filters: {error_msg}"
            elif "QUOTA" in error_msg.upper() or "RATE" in error_msg.upper():
                error_msg = f"Rate limit or quota exceeded: {error_msg}"
            
            return LLMResponse(
                content="",
                latency_ms=latency_ms,
                model=self.model,
                error=error_msg,
            )
