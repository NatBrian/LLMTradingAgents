"""
Google Gemini LLM client implementation.

Uses the google-genai library for direct Gemini API access.
"""

import os
import time
from typing import Optional

from .base import LLMClient, LLMResponse
import logging

logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    """Google Gemini API client"""
    
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
            from google import genai
            from google.genai import types
            self._genai_types = types
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "google-genai package required. Install with: pip install google-genai"
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
        
        logger.debug("Sending Gemini request", extra={"model": self.model, "json_mode": json_mode})
        
        start_time = time.time()
        
        # Build configuration
        config_args = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if json_mode:
            config_args["response_mime_type"] = "application/json"
            
        if system_prompt:
            config_args["system_instruction"] = system_prompt

        # Retry logic
        max_retries = 3
        retry_delay = 2.0
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Generate response
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=self._genai_types.GenerateContentConfig(**config_args),
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                logger.debug("Gemini response received", extra={"latency_ms": latency_ms})
                
                # Extract content
                content = ""
                if hasattr(response, 'text') and response.text:
                    content = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Fallback for complex responses
                    parts = []
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            parts.append(part.text)
                    content = "".join(parts)
                
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
                last_error = e
                is_last_attempt = attempt == max_retries
                
                if not is_last_attempt:
                    logger.warning(
                        f"Gemini request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {retry_delay}s...", 
                        extra={"error": str(e), "attempt": attempt + 1}
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Last attempt failed
                    pass

        # If we get here, all retries failed
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Gemini request failed after {max_retries + 1} attempts: {last_error}", extra={"error": str(last_error)})
        error_msg = str(last_error)
        
        # Handle specific Gemini errors
        if "SAFETY" in error_msg.upper():
            error_msg = f"Content blocked by safety filters: {error_msg}"
        elif "QUOTA" in error_msg.upper() or "RATE" in error_msg.upper() or "429" in error_msg:
            error_msg = f"Rate limit or quota exceeded: {error_msg}"
        
        return LLMResponse(
            content="",
            latency_ms=latency_ms,
            model=self.model,
            error=error_msg,
        )
