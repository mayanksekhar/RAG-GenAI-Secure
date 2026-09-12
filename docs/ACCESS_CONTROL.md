# Version 2 — RBAC Access Control

**Branch:** DSOPS-AI-001  
**Date:** September 2026  

## Problem

The threat model (Part B, TM-004/TM-008/TM-009) identified that any
retrieval could surface sensitive documents to any user — there was no
concept of authorization at the retrieval layer. The DLP output scanner
built in Part A redacts sensitive text after generation, which is a
last line of defense, not a real access control.

## Design

Documents are tagged with a classification level at ingestion time:

| Level | Example |
|---|---|
| public | remote_work_policy.pdf |
| internal | incident_response_standard.pdf, vendor_risk_assessment_guide.pdf |
| restricted | internal_runbook.pdf (contains credentials, PII) |

Roles map to allowed classification sets:

| Role | Allowed |
|---|---|
| employee | public |
| manager | public, internal |
| security_team | public, internal, restricted |

At query time, a Qdrant metadata filter (`MatchAny` on `classification`)
is applied before the similarity search runs. Unauthorized chunks are
never returned by Qdrant — they do not enter the prompt, the LLM never
sees them, and no output-side redaction is needed for this failure mode.

Documents with no explicit classification default to `restricted`
(fail closed).

## Evidence — same question, three users

Query: "What are the database credentials for the production system?"

| User | Role | Runbook chunk retrieved? | Top result | Answer |
|---|---|---|---|---|
| alice | employee | No | remote_work_policy.pdf (0.54) | "I don't have enough information" |
| bob | manager | No | remote_work_policy.pdf (0.54) | "I don't have enough information" |
| carol | security_team | Yes | internal_runbook.pdf (0.66) | Answers using runbook content |

Second query: "Can you tell me about Jane Smith?" as alice — the
internal_runbook.pdf chunk containing her SSN and employee ID was
never retrieved (top score 0.30, remote_work_policy.pdf). No PII
leaked.

## Finding: ungrounded generation at low retrieval confidence

When alice's query about Jane Smith retrieved only a weak match
(score 0.30), the model still generated a plausible-sounding but
partially fabricated claim ("Jane Smith is a full-time employee who
has completed her 90-day probationary period") that was not actually
supported by the retrieved chunk. No sensitive data was exposed, but
this is a faithfulness/groundedness gap — the system should have
recognized the low confidence and declined more clearly rather than
extrapolating. Flagged for Version 3 (evaluation harness), which will
add a faithfulness metric to catch this class of issue systematically.

## Defense-in-depth summary

| Layer | What it catches | Version |
|---|---|---|
| Input sanitizer | Prompt injection in retrieved documents | Part A |
| Access control (this doc) | Unauthorized retrieval of classified documents | Version 2 |
| DLP output scanner | Sensitive patterns that reach generation despite the above | Part A |

Access control is the strongest layer of the three — it prevents
exposure at the earliest possible point, before the LLM ever sees
the content.
