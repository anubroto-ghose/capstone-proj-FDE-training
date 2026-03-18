# Token Optimization via LLMLingua prompt compression
# This module compresses long conversation contexts before sending to the LLM
# to reduce token usage and cost in bulk incident analysis scenarios.

import os
from typing import Optional

# LLMLingua is optional — gracefully degrade if not installed
try:
    from llmlingua import PromptCompressor
    _compressor = PromptCompressor(
        model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
        use_llmlingua2=True,
        device_map="cpu",
    )
    LLMLINGUA_AVAILABLE = True
except Exception:
    _compressor = None
    LLMLINGUA_AVAILABLE = False


def compress_prompt(
    context: str,
    instruction: str,
    target_token_rate: float = 0.5,
    force_tokens: Optional[list] = None,
) -> str:
    """
    Compresses a long context string using LLMLingua-2 to reduce tokens
    while preserving the key information.

    Falls back to truncation if LLMLingua is unavailable.

    Args:
        context: The text to compress (e.g., conversation history or retrieved docs).
        instruction: The task instruction (kept verbatim, not compressed).
        target_token_rate: Target compression ratio (0.5 = compress to ~50% of tokens).
        force_tokens: Optional list of tokens that must not be removed.

    Returns:
        The compressed context string.
    """
    if not context or not context.strip():
        return context

    if LLMLINGUA_AVAILABLE and _compressor is not None:
        try:
            result = _compressor.compress_prompt(
                context.split("\n"),
                instruction=instruction,
                question="",
                target_token=int(len(context.split()) * target_token_rate),
                force_tokens=force_tokens or [],
            )
            return result.get("compressed_prompt", context)
        except Exception:
            pass  # Fall through to truncation

    # Fallback: simple truncation to ~60% of words
    words = context.split()
    cutoff = int(len(words) * target_token_rate)
    return " ".join(words[:cutoff])


def compress_history_for_bulk_analysis(messages: list, target_rate: float = 0.4) -> str:
    """
    Takes a list of message dicts (role/content) and returns a compressed
    string suitable for bulk incident analysis, stripping out boilerplate
    and keeping only substantive content.
    """
    # Build a flat text from non-trivial messages
    lines = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if not content or len(content.strip()) < 10:
            continue
        lines.append(f"[{role.upper()}]: {content.strip()}")

    full_text = "\n".join(lines)
    return compress_prompt(full_text, instruction="Summarize IT incident conversation", target_token_rate=target_rate)
