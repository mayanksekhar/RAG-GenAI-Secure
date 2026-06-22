# Threat Model — RAG-GenAI-Secure

**Application:** Acme Corp Internal Policy RAG Chatbot  
**Version:** 1.0  
**Date:** June 2026  
**Author:** Mayank Shekhar Singh  
**Methodology:** STRIDE  
**Scope:** Local deployment on `son-of-anton` (Fedora 44), self-hosted Qdrant, local Ollama inference  

---

## 1. Architecture Overview

```
User Query
    │
    ▼
[Query Script] ──► [Ollama: nomic-embed-text]  (embedding)
    │
    ▼
[Qdrant Vector DB] ◄──── [Ingest Script] ◄──── [PDF Source Docs]
    │                          │
    │                    [Ollama: nomic-embed-text]
    ▼
[Retrieved Chunks]
    │
    ▼
[Prompt Constructor] ──► [Ollama: llama3 / llama3.2:1b]  (generation)
    │
    ▼
[Output Scanner (DLP)]
    │
    ▼
User Response
```

### Components

| Component | Technology | Trust Level |
|---|---|---|
| Query interface | Python CLI (`src/query.py`) | Trusted (internal only) |
| Embedding model | Ollama `nomic-embed-text` | Trusted (local) |
| LLM | Ollama `llama3` / `llama3.2:1b` | Trusted (local) |
| Vector database | Qdrant (Docker, port 6333/6334) | Trusted (local, no auth) |
| Document corpus | PDF files in `data/source_docs/` | **Untrusted** (could be user-submitted) |
| Ingest script | Python (`src/ingest.py`) | Trusted (internal only) |
| Input sanitizer | Python (`src/sanitizer.py`) | Trusted (internal) |
| Output scanner | Python (`src/output_scanner.py`) | Trusted (internal) |

---

## 2. Trust Boundaries

1. **User → Query script**: user input is untrusted; direct prompt injection possible
2. **Document corpus → Ingest pipeline**: document content is untrusted; indirect prompt injection possible
3. **Qdrant API → Query script**: currently no authentication; local network exposure
4. **Ollama API → Scripts**: unauthenticated local HTTP; no TLS

---

## 3. STRIDE Threat Analysis

### 3.1 Component: User Query Input

| STRIDE Category | Threat | Risk | Status |
|---|---|---|---|
| **S**poofing | Attacker impersonates a privileged user to extract restricted policy content | Medium | ⚠️ Open — no authentication on query interface |
| **T**ampering | User injects instructions directly into the query to override system prompt (direct prompt injection) | High | ⚠️ Open — partial mitigation via system prompt; no input validation on raw query |
| **R**epudiation | No audit log of queries made; attacker covers tracks | Medium | ⚠️ Open — no query logging implemented |
| **I**nformation Disclosure | User crafts a query to extract sensitive content from corpus (data leakage) | High | ✅ Mitigated — DLP output scanner redacts known sensitive patterns |
| **D**enial of Service | Flood of queries exhausts Ollama inference capacity; CPU-bound model has low throughput | Medium | ⚠️ Open — no rate limiting |
| **E**levation of Privilege | User gains ability to re-index corpus by accessing ingest script directly | Low | ⚠️ Open — no access control on scripts |

---

### 3.2 Component: Document Corpus (PDF files)

| STRIDE Category | Threat | Risk | Status |
|---|---|---|---|
| **S**poofing | Attacker submits a malicious PDF disguised as a legitimate policy document | High | ⚠️ Open — no document provenance or signing |
| **T**ampering | Attacker modifies an existing policy PDF to embed injection payloads (indirect prompt injection) | High | ✅ Mitigated — input sanitizer strips known injection patterns from retrieved chunks |
| **R**epudiation | No record of who submitted which document or when | Medium | ⚠️ Open — no document audit trail |
| **I**nformation Disclosure | Sensitive documents (runbooks, HR files) inadvertently added to corpus and exposed via queries | High | ✅ Partially mitigated — DLP scanner redacts output; root cause (corpus access control) unaddressed |
| **D**enial of Service | Corpus flooded with large PDFs, exhausting Qdrant storage or embedding throughput | Low | ⚠️ Open — no file size or volume limits on ingest |
| **E**levation of Privilege | Injected document instructs LLM to perform privileged actions (e.g. reveal system config) | High | ✅ Mitigated — input sanitizer; LLM has no tool-calling or privileged access in current config |

---

### 3.3 Component: Qdrant Vector Database

| STRIDE Category | Threat | Risk | Status |
|---|---|---|---|
| **S**poofing | Any process on localhost can connect as if it were the application | High | ⚠️ Open — no API key or authentication configured |
| **T**ampering | Attacker with localhost access modifies or deletes vector collections | High | ⚠️ Open — no auth, no write controls |
| **R**epudiation | No audit log of Qdrant operations | Medium | ⚠️ Open |
| **I**nformation Disclosure | All indexed document chunks (including sensitive content) readable by any localhost process | High | ⚠️ Open — no auth on Qdrant REST API (port 6333) |
| **D**enial of Service | Collection deleted or corrupted by unauthorized process | Medium | ⚠️ Open |
| **E**levation of Privilege | Not applicable — Qdrant has no privilege model in current config | N/A | N/A |

---

### 3.4 Component: Ollama LLM API

| STRIDE Category | Threat | Risk | Status |
|---|---|---|---|
| **S**poofing | Any process on localhost can send inference requests | Medium | ⚠️ Open — Ollama listens on 127.0.0.1:11434, no auth |
| **T**ampering | Prompt content manipulated in transit (localhost, low risk) | Low | ✅ Acceptable — local loopback only |
| **R**epudiation | No logging of prompts sent to Ollama | Medium | ⚠️ Open |
| **I**nformation Disclosure | Full augmented prompt (including retrieved sensitive chunks) visible to any localhost process | Medium | ⚠️ Open |
| **D**enial of Service | Resource exhaustion via large prompt or parallel inference requests | Medium | ⚠️ Open — no rate limiting; CPU-bound inference has low capacity |
| **E**levation of Privilege | Not applicable in current config | N/A | N/A |

---

## 4. Risk Summary

| Finding ID | Component | Threat | STRIDE | Risk | Status |
|---|---|---|---|---|---|
| TM-001 | Query input | Direct prompt injection | T | High | ⚠️ Open |
| TM-002 | Document corpus | Indirect prompt injection via poisoned PDF | T | High | ✅ Mitigated |
| TM-003 | Document corpus | Sensitive data leakage via corpus | I | High | ✅ Partially mitigated |
| TM-004 | Qdrant | No authentication on vector DB API | S/I/T | High | ⚠️ Open |
| TM-005 | Document corpus | No document provenance / signing | S | High | ⚠️ Open |
| TM-006 | Query interface | No query audit logging | R | Medium | ⚠️ Open |
| TM-007 | All components | No rate limiting on inference or query | D | Medium | ⚠️ Open |
| TM-008 | Qdrant | Sensitive chunks readable without auth | I | High | ⚠️ Open |
| TM-009 | Query interface | No user authentication | S | Medium | ⚠️ Open |
| TM-010 | Ollama API | No prompt logging or audit trail | R | Medium | ⚠️ Open |

---

## 5. Mitigations Implemented

| Finding ID | Mitigation | Implementation |
|---|---|---|
| TM-002 | Input sanitizer strips injection patterns from retrieved chunks | `src/sanitizer.py` |
| TM-003 | DLP output scanner redacts known sensitive patterns before response | `src/output_scanner.py` |

---

## 6. Accepted Risks (Dev Environment)

The following risks are accepted for this local development deployment and would require remediation before any production deployment:

- **TM-004** — Qdrant auth: acceptable on localhost dev; production requires API key + TLS
- **TM-009** — No user auth: CLI tool, single user; production requires AuthN/AuthZ layer
- **TM-007** — No rate limiting: single-user dev; production requires rate limiting middleware

---

## 7. Recommended Next Controls (Production Roadmap)

1. Enable Qdrant API key authentication and restrict network exposure
2. Add user authentication layer before query interface
3. Implement query audit logging (user, timestamp, question, retrieved sources)
4. Add document provenance controls — only signed/approved documents ingested
5. Implement corpus access control — segment sensitive documents from general queries
6. Add rate limiting on inference endpoint
7. Deploy prompt logging for security monitoring and incident response
