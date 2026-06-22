"""
Output scanner: scans LLM responses for sensitive data patterns before
returning them to the user.

In production this would be backed by a dedicated DLP (Data Loss Prevention)
service. This is a demonstration-grade regex implementation showing the
concept and the integration point.
"""

import re

SENSITIVE_PATTERNS = [
    (r'sk_live_[A-Za-z0-9_]{10,}', 'Stripe live API key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS access key ID'),
    (r'postgresql://\S+:\S+@\S+', 'Database connection string with credentials'),
    (r'mysql://\S+:\S+@\S+', 'Database connection string with credentials'),
    (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN pattern'),
    (r'(?i)(password|secret|credential)\s*[:=]\s*\S+', 'Credential pattern'),
    (r'(?i)salary\s+band\s+[A-Z0-9]+', 'Salary information'),
    (r'employee\s+ID\s+[A-Z0-9\-]+', 'Employee ID'),
]

COMPILED = [(re.compile(p), label) for p, label in SENSITIVE_PATTERNS]


def scan_output(text: str) -> tuple[str, list[str]]:
    """
    Scans response text for sensitive data patterns.
    Returns (redacted_text, list_of_findings).
    Findings are logged; text is redacted before returning to user.
    """
    findings = []
    redacted = text

    for pattern, label in COMPILED:
        matches = pattern.findall(redacted)
        if matches:
            findings.append(f"{label}: {len(matches)} match(es) detected and redacted")
            redacted = pattern.sub(f"[REDACTED: {label}]", redacted)

    return redacted, findings
