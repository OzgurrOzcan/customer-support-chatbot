"""
Text Sanitizer — Prompt injection detection and LLM input sanitization.

Detects common prompt injection patterns where an attacker
tries to override the system prompt or inject new instructions.
Also wraps context text with delimiters to prevent manipulation.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Known prompt injection patterns (case-insensitive)
INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)",
    r"disregard\s+(all\s+)?(previous|above|prior)",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"system\s*:\s*",
    r"<\|system\|>",
    r"act\s+as\s+(?:a|an)\s+",
    r"forget\s+(everything|all|your|previous)",
    r"new\s+instructions?\s*:",
    r"override\s+(your|system|all)\s+",
    r"pretend\s+(you|that|to)\s+",
    r"jailbreak",
    r"DAN\s+mode",
]

# Compile for performance (compiled once at module load)
_compiled_patterns = [
    re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
]


def detect_prompt_injection(text: str) -> bool:
    """Check if text contains prompt injection attempts.

    Args:
        text: The user's query text.

    Returns:
        True if a prompt injection pattern is detected.
    """
    for pattern in _compiled_patterns:
        if pattern.search(text):
            logger.warning(
                f"Prompt injection detected | pattern={pattern.pattern} | "
                f"text='{text[:80]}...'"
            )
            return True
    return False


def sanitize_for_llm(context_text: str) -> str:
    """Wrap context text with delimiters to prevent prompt injection.

    By enclosing the context in triple-hash delimiters,
    we instruct the LLM to treat everything inside as
    data — not instructions.

    Args:
        context_text: The context text from Pinecone search.

    Returns:
        Sanitized context text with delimiters.
    """
    return f"###\n{context_text}\n###"
