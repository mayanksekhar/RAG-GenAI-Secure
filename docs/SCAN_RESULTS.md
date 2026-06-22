# SAST and SCA Scan Results

**Date:** June 2026  
**Tools:** Semgrep 1.x (SAST), pip-audit 2.10.1 (SCA)  

## SAST — Semgrep

- Rules run: 290 (auto) + 151 (python ruleset)
- Files scanned: 5 (src/)
- Findings: 0

Zero findings consistent with codebase using no dangerous patterns —
no SQL queries, no shell injection, no eval(), no hardcoded credentials
in source files. Credentials exist only in test fixtures (fake secrets
planted deliberately for the data leakage exercise in Part A).

## SCA — pip-audit

- Packages audited: all venv dependencies
- Known CVEs found: 0

All dependencies installed from PyPI at current versions (June 2026).
No known vulnerabilities in the dependency tree at time of scan.

## Notes

- SAST scope limited to src/ — scripts/ directory excluded (attack
  simulation scripts, not production code)
- SCA scans the full venv; requirements.txt pins all versions
- Scans should be re-run on every dependency update
- For CI automation of these scans, see .gitlab-ci.yml
