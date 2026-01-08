"""
Abstract base class for agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from ..llm.base import LLMClient, LLMResponse


@dataclass
class AgentResult:
    """Result from an agent invocation."""
    success: bool
    output: Any  # Parsed schema object (StrategistProposal or TradePlan)
    raw_response: str = ""
    prompt: str = ""  # Input prompt
    system_prompt: str = ""  # System prompt
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    error: Optional[str] = None


class Agent(ABC):
    """
    Abstract base class for LLM-powered agents.
    
    Each agent has:
    - A role (what it does)
    - A system prompt (how it should behave)
    - An invoke method (execute the agent on input)
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the agent.
        
        Args:
            llm_client: The LLM client to use for generation
        """
        self.llm_client = llm_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name."""
        pass
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Return a brief description of the agent's role."""
        pass
    
    @abstractmethod
    def invoke(self, context: dict) -> AgentResult:
        """
        Invoke the agent with the given context.
        
        Args:
            context: Dictionary containing agent-specific inputs
            
        Returns:
            AgentResult with the parsed output (or error)
        """
        pass
    
    def _parse_response(self, response: LLMResponse, model_class: type, prompt: str = "", system_prompt: str = "") -> AgentResult:
        """
        Parse an LLM response into a Pydantic model.
        
        Args:
            response: The raw LLM response
            model_class: The Pydantic model class to parse into
            prompt: The input prompt used for generation
            system_prompt: The system prompt used for generation
            
        Returns:
            AgentResult with parsed output or error
        """
        if not response.success:
            return AgentResult(
                success=False,
                output=None,
                raw_response=response.content,
                prompt=prompt,
                system_prompt=system_prompt,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=response.latency_ms,
                error=response.error,
            )
        
        try:
            # Clean content (strip markdown code blocks)
            content = self._clean_json_string(response.content)
            
            parsed = model_class.model_validate_json(content)
            return AgentResult(
                success=True,
                output=parsed,
                raw_response=response.content,
                prompt=prompt,
                system_prompt=system_prompt,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=response.latency_ms,
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                raw_response=response.content,
                prompt=prompt,
                system_prompt=system_prompt,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=response.latency_ms,
                error=f"JSON parse error: {e}",
            )

    def _clean_json_string(self, content: str) -> str:
        """
        Clean JSON string by removing markdown code blocks.
        
        LLMs often wrap JSON in ```json ... ``` blocks.
        """
        content = content.strip()
        
        # Remove ```json or ``` at start
        if content.startswith("```"):
            # Find first newline
            newline_idx = content.find("\n")
            if newline_idx != -1:
                content = content[newline_idx+1:]
            else:
                # Fallback if no newline (rare)
                if content.startswith("```json"):
                    content = content[7:]
                else:
                    content = content[3:]
        
        # Remove ``` at end
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()
