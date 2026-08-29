---
name: Bug report
about: Something does not work as documented
labels: bug
---

**What happened**

**What you expected**

**How to reproduce**
Use a synthetic report from `samples/` — never real patient data.

**Environment**
- OS and browser:
- Python version:
- Client build (browser console shows `[PlainMed] client build ...`):
- Backend (`GET /api/v1/health` reports `llm_backend` and `ocr_backend`):

**Checks**
Did these pass? `python -m pytest`, `offline_check.py`, `retention_check.py`,
`deident_check.py`
