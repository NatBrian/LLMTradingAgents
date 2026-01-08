"""
Prompt templates for LLM calls.

NOTE: The 3-agent system (Strategist + Risk Guard) prompts are defined
directly in the agents module to avoid circular imports:
    - myllmtradingagents.agents.strategist (STRATEGIST_SYSTEM_PROMPT, etc.)
    - myllmtradingagents.agents.risk_guard (RISK_GUARD_SYSTEM_PROMPT, etc.)
"""

import json


# ============================================================================
# JSON Repair Prompt
# ============================================================================

REPAIR_SYSTEM_PROMPT = """You are a JSON repair assistant. The user will provide malformed JSON that failed to parse.
Your job is to fix the JSON so it is valid and matches the expected schema.

RULES:
1. Output ONLY valid JSON. No explanations, no markdown.
2. Preserve the intent and data from the original as much as possible.
3. If fields are missing, add them with sensible defaults.
4. If there are syntax errors (missing quotes, brackets, commas), fix them.

Expected schema:
{schema}
"""

REPAIR_USER_PROMPT = """Fix this malformed JSON:

{malformed_json}

Parse error: {error}

Output ONLY the corrected JSON object."""


def build_repair_prompt(
    malformed_json: str,
    error: str,
    schema: dict,
) -> tuple[str, str]:
    """
    Build a prompt to repair malformed JSON.
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = REPAIR_SYSTEM_PROMPT.format(
        schema=json.dumps(schema, indent=2)
    )
    
    user_prompt = REPAIR_USER_PROMPT.format(
        malformed_json=malformed_json,
        error=error,
    )
    
    return system_prompt, user_prompt
