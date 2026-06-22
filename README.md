# RAG-GenAI-Secure

A portfolio project demonstrating **DevSecOps and AI/GenAI security** skills,
built as a hands-on showcase for a senior security leadership role.

The project has two parts: building and attacking a RAG-based AI application
(Part A), and running it through a formal application security program (Part B).

---

## Part A — AI / GenAI Security

A retrieval-augmented generation (RAG) pipeline built on a fully self-hosted
local stack, then deliberately attacked and hardened.

### Stack

| Component | Technology |
|---|---|
| LLM inference | Ollama (`llama3`, `llama3.2:1b`) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector database | Qdrant (Docker, self-hosted) |
| RAG framework | LlamaIndex |
| Runtime | Python 3.12 |
| Host | Fedora 44 ThinkPad X1 Carbon (`son-of-anton`) |

### Attack Scenarios Demonstrated

**Attack 1 — Indirect Prompt Injection (OWASP LLM01)**
- Planted a malicious instruction inside a vendor policy PDF
- Showed the instruction being retrieved and executed by the LLM,
  causing it to refuse legitimate user questions
- Fixed with a regex-based input sanitizer (`src/sanitizer.py`) that
  strips injection patterns from retrieved chunks before prompt construction

**Attack 2 — Sensitive Data Leakage (OWASP LLM06)**
- Planted fake database credentials, API keys, and PII in a runbook document
- Showed the LLM leaking the full PostgreSQL connection string and SSN
  verbatim in response to direct queries
- Fixed with a DLP output scanner (`src/output_scanner.py`) that detects
  and redacts sensitive patterns before the response reaches the user

### Key Files
src/

ingest.py          # PDF ingestion → chunking → embedding → Qdrant

query.py           # Query → retrieval → augmented prompt → LLM response

sanitizer.py       # Input sanitizer: strips prompt injection patterns

output_scanner.py  # Output DLP scanner: redacts sensitive data patterns

scripts/

plant_injection.py # Attack 1: generates a poisoned PDF

plant_leakage.py   # Attack 2: generates a document with planted secrets

data/source_docs/    # Acme Corp synthetic policy documents (corpus)

---

## Part B — Application Security Program

The same application put through a formal enterprise AppSec gate.

### Controls Implemented

| Control | Tool | Status |
|---|---|---|
| Threat modeling | STRIDE | ✅ Complete — 4 components, 10 threats |
| Static code analysis | Semgrep | ✅ Automated in CI |
| Dependency scanning | pip-audit | ✅ Automated in CI |
| CI/CD security pipeline | GitLab CI + GitHub Actions | ✅ Live |
| Vulnerability tracking | VULN_TRACKER.md | ✅ 18 findings tracked |
| Metrics reporting | METRICS_SUMMARY.md | ✅ Leadership-ready |

### CI Pipelines

Both platforms run SAST (Semgrep) and SCA (pip-audit) automatically
on every push to `main`.

- **GitLab CI**: self-hosted runner on `son-of-anton` (Docker executor)
- **GitHub Actions**: GitHub-hosted Ubuntu runner

### Key Documents

docs/

THREAT_MODEL.md     # STRIDE threat model — 10 findings across 4 components

VULN_TRACKER.md     # Full vulnerability tracker — 18 findings, severity, status

SCAN_RESULTS.md     # SAST and SCA scan results summary

METRICS_SUMMARY.md  # Leadership metrics one-pager

.gitlab-ci.yml        # GitLab CI pipeline

.github/workflows/

security-scans.yml  # GitHub Actions workflow

---

## Real Engineering Issues Encountered and Resolved

This project was built hands-on. Real issues hit along the way:

- **SELinux blocking Qdrant volume mount** — fixed with `:Z` Docker flag
- **ROCm GPU detection failure** — Intel iGPU on X1 Carbon; no AMD GPU;
  confirmed CPU-only inference path and documented as a known constraint
- **llama3 CPU timeout** — switched to `llama3.2:1b` for development;
  llama3 retained for final demo use
- **SimpleDirectoryReader reading raw PDF bytes silently** — fixed by
  installing `llama-index-readers-file`; root cause documented
- **Python 3.14 numpy wheel unavailable** — downgraded project venv to
  Python 3.12 where all ML ecosystem wheels are prebuilt

---

## Running Locally

```bash
# Prerequisites: Docker, Ollama, Python 3.12

# Start Qdrant
docker run -d --name qdrant -p 6333:6333 \
  -v ~/qdrant_storage:/qdrant/storage:Z qdrant/qdrant

# Pull models
ollama pull llama3.2:1b
ollama pull nomic-embed-text

# Install dependencies
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Ingest documents
python src/ingest.py

# Query
python src/query.py "What is required of Tier 1 vendors?"
```

---

## Frameworks Referenced

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [STRIDE Threat Modeling](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- NIST AI RMF (Govern, Map, Measure, Manage)
