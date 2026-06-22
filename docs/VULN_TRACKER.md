# Vulnerability Tracker — RAG-GenAI-Secure

**Last Updated:** June 2026  
**Owner:** Mayank Shekhar Singh  
**Sources:** STRIDE Threat Model, Semgrep SAST, pip-audit SCA  

---

## Summary

| Severity | Total | Open | Mitigated | Accepted |
|---|---|---|---|---|
| High | 10 | 6 | 3 | 1 |
| Medium | 7 | 5 | 0 | 2 |
| Low | 1 | 1 | 0 | 0 |
| **Total** | **18** | **12** | **3** | **3** |

---

## Findings

| ID | Source | Component | Title | Severity | Status | Fix / Notes |
|---|---|---|---|---|---|---|
| TM-001 | Threat Model | Query input | Direct prompt injection via user query | High | Open | Add input validation on raw query before embedding |
| TM-002 | Threat Model | Document corpus | Indirect prompt injection via poisoned PDF | High | Mitigated | src/sanitizer.py strips injection patterns from retrieved chunks |
| TM-003 | Threat Model | Document corpus | Sensitive data leakage via corpus | High | Partially mitigated | src/output_scanner.py redacts output; corpus access control still needed |
| TM-004 | Threat Model | Qdrant | No authentication on vector DB API | High | Accepted (dev) | Production: enable Qdrant API key + TLS |
| TM-005 | Threat Model | Document corpus | No document provenance or signing | High | Open | Implement document signing and allowlist before ingest |
| TM-006 | Threat Model | Query interface | No query audit logging | Medium | Open | Add structured logging: user, timestamp, question, sources |
| TM-007 | Threat Model | All components | No rate limiting on inference or query | Medium | Accepted (dev) | Production: add rate limiting middleware |
| TM-008 | Threat Model | Qdrant | Sensitive chunks readable without auth | High | Open | Blocked on TM-004 fix |
| TM-009 | Threat Model | Query interface | No user authentication | Medium | Accepted (dev) | Production: AuthN/AuthZ layer required |
| TM-010 | Threat Model | Ollama API | No prompt logging or audit trail | Medium | Open | Add prompt logging for security monitoring |
| SCA-001 | pip-audit (CI) | pip 25.0.1 | CVE-2025-8869 | High | Mitigated | pip upgraded to 26.1.2 in CI pipeline |
| SCA-002 | pip-audit (CI) | pip 25.0.1 | CVE-2026-1703 | High | Mitigated | pip upgraded to 26.1.2 in CI pipeline |
| SCA-003 | pip-audit (CI) | pip 25.0.1 | CVE-2026-3219 | High | Mitigated | pip upgraded to 26.1.2 in CI pipeline |
| SCA-004 | pip-audit (CI) | pip 25.0.1 | CVE-2026-6357 | High | Mitigated | pip upgraded to 26.1.2 in CI pipeline |
| SCA-005 | pip-audit (CI) | pip 25.0.1 | PYSEC-2026-196 | High | Mitigated | pip upgraded to 26.1.2 in CI pipeline |
| SAST-000 | Semgrep | src/ | Zero findings across 290 rules | Info | Closed | Clean result — no dangerous patterns in source code |
| TM-011 | Threat Model | Docker | Qdrant container has no resource limits | Low | Open | Add --memory and --cpus limits to docker run command |
| TM-012 | Threat Model | All components | No secrets management — API keys hardcoded if added | Medium | Open | Use environment variables or a secrets manager for any future API keys |

---

## Remediation Roadmap

### Immediate (before any production deployment)
- TM-001: Add input validation on user queries
- TM-004 / TM-008: Enable Qdrant API key authentication
- TM-005: Implement document provenance controls

### Short term (within 30 days)
- TM-006: Add query audit logging
- TM-010: Add prompt logging
- TM-012: Move any secrets to environment variables

### Accepted for dev environment
- TM-007: Rate limiting (single user, local dev)
- TM-009: User authentication (CLI tool, local dev)

---

## MTTR Snapshot

| Category | Findings | Remediated | MTTR |
|---|---|---|---|
| SCA (pip CVEs) | 5 | 5 | Same day (1 commit) |
| AI Security (Part A) | 2 | 2 | Same session |
| Threat Model findings | 10 | 1 | Ongoing |
