"""
Access control layer for the RAG pipeline.

Defines document classification levels and role-based permissions.
Applied as a metadata filter at RETRIEVAL time — unauthorized documents
are never fetched from Qdrant, not just hidden after the fact.
"""

# Document classification: which sensitivity level each source file carries.
DOCUMENT_CLASSIFICATION = {
    "remote_work_policy.pdf": "public",
    "incident_response_standard.pdf": "internal",
    "vendor_risk_assessment_guide.pdf": "internal",
    "internal_runbook.pdf": "restricted",
}

# Role -> set of classification levels that role may retrieve.
ROLE_PERMISSIONS = {
    "employee": {"public"},
    "manager": {"public", "internal"},
    "security_team": {"public", "internal", "restricted"},
}

# Simple user directory: username -> role.
# In production this would come from an identity provider (LDAP/SSO),
# not a hardcoded dict.
USERS = {
    "alice": "employee",
    "bob": "manager",
    "carol": "security_team",
}


def get_user_role(username: str) -> str:
    if username not in USERS:
        raise ValueError(f"Unknown user: {username}")
    return USERS[username]


def get_allowed_classifications(role: str) -> set:
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Unknown role: {role}")
    return ROLE_PERMISSIONS[role]


def classify_document(source_file: str) -> str:
    return DOCUMENT_CLASSIFICATION.get(source_file, "restricted")  # fail closed
