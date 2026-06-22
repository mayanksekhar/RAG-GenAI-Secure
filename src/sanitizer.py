"""
Input sanitizer for retrieved chunks before they enter the prompt.

Scans chunk text for instruction-injection patterns and either strips
the malicious content or flags the chunk for rejection.

This is a demonstration-grade implementation — production systems would
use a secondary LLM classifier or a dedicated guardrails library
(e.g. NeMo Guardrails, Guardrails AI) for more robust detection.
"""

import re

INJECTION_PATTERNS = [
    r"\[SYSTEM\s*:",
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+in\s+.{0,30}\s+mode",
    r"do\s+not\s+reveal\s+these\s+instructions",
    r"respond\s+only\s+with",
    r"maintenance\s+mode",
    r"new\s+instructions?\s*:",
    r"disregard\s+(all\s+)?prior",
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def contains_injection(text: str) -> bool:
    return any(p.search(text) for p in COMPILED)


def sanitize_chunk(text: str) -> tuple[str, bool]:
    """
    Returns (sanitized_text, was_modified).
    Strips content between injection markers where possible.
    """
    if not contains_injection(text):
        return text, False

    cleaned = re.sub(r'\[SYSTEM\s*:.*?\]', '[CONTENT REMOVED BY SECURITY FILTER]', text, flags=re.IGNORECASE | re.DOTALL)
    return cleaned, True


def sanitize_chunks(chunks) -> list:
    """
    Takes a list of Qdrant ScoredPoint chunks, sanitizes each one,
    logs any detections, and returns the cleaned list.
    """
    clean = []
    for chunk in chunks:
        text = chunk.payload.get("text", "")
        source = chunk.payload.get("source_file", "unknown")
        sanitized, modified = sanitize_chunk(text)

        if modified:
            print(f"  [SECURITY] Injection pattern detected and stripped in: {source}")
            chunk.payload["text"] = sanitized
            chunk.payload["sanitized"] = True

        clean.append(chunk)
    return clean
