# Data Protection Impact Assessment — PlainMed

> **DRAFT for DPO / counsel completion.** A DPIA is mandatory here: GDPR
> Art. 35(3)(b) triggers on large-scale processing of special-category
> (health) data. This draft supplies the engineering facts and an initial
> risk assessment. Sign-off, residual-risk acceptance, and the decision on
> whether prior consultation with a supervisory authority is required
> (Art. 36) are not engineering decisions.

**Version 2026-08-28 · Status: DRAFT, unsigned**

## 1. Description of processing

**What.** Users photograph or upload a laboratory report. PlainMed extracts
the test values, explains them in plain language with links back to the
source lines, and generates questions to ask a clinician.

**Categories of data.** Health data (special category, Art. 9): laboratory
test results. Incidentally, whatever identifiers appear on the uploaded
report — name, date of birth, record number, address, clinician name.

**Data subjects.** Adults who choose to upload their own report, or a report
they are authorised to act for.

**Scale.** [COMPLETE: expected users per month.] Note that Art. 35(3)(b)
applies to *large-scale* processing; document your estimate and reasoning.

**Retention.** Report data: duration of the request only, held in memory.
Audit records: [RETENTION PERIOD], containing no report content.

**Recipients.** [CLOUD HOST] (trusted tier, sees report content, under
[BAA/DPA]); [GPU PROVIDER] (model tier, receives de-identified values only);
[LOG PROVIDER] (audit records, no report content).

**Transfers.** [COMPLETE: countries and transfer mechanism.]

## 2. Necessity and proportionality

**Purpose.** Helping patients understand their own medical reports, which
they already lawfully hold.

**Is processing necessary?** Yes — the report must be read to be explained.

**Is it proportionate?** The design minimises processing well beyond the
default for this class of product:

- No accounts, so no user profile exists to be breached.
- No storage of report content, so there is no database to exfiltrate.
- Identifiers removed before the AI model, so the model tier never processes
  identifiable data.
- No analytics, telemetry, or third-party assets.

**Alternatives considered.** Fully on-device inference would eliminate
transmission entirely, but MedGemma 4B does not fit acceptably on typical
consumer phones. The trusted/model tier split was adopted as the closest
achievable approximation: identifiers never leave the trusted tier.

## 3. Risks and mitigations

| # | Risk | Likelihood | Severity | Mitigation | Residual |
|---|---|---|---|---|---|
| 1 | Report intercepted in transit | Low | High | TLS 1.2+ enforced; HSTS | Low |
| 2 | Report persisted by accident (log, temp file, crash dump) | Medium | High | No file writes in request path; PHI log filter; `retention_check.py` runs in CI | Low |
| 3 | Identifiers reach the model tier | Low | High | Allowlist de-identification, re-verified post-construction; `deident_check.py` in CI | Low |
| 4 | Third-party SDK captures request bodies | **Medium** | High | Policy: no telemetry SDKs. **Not technically enforced** — see below | **Medium** |
| 5 | User acts on a wrong explanation | Medium | **High** | Confirm-before-explain step; low-confidence flagging; validation rejects unsupported claims; prominent disclaimers | Medium |
| 6 | OCR misreads a value | **High** | High | Review screen with editable values; confidence flagging on numeric tokens; source lines shown | Medium |
| 7 | Host or infrastructure compromise exposes memory | Low | High | Hardening, least privilege, patching | Low–Medium |
| 8 | Re-identification from lab values alone | Low | Medium | Only values crossing the boundary; no dates, no free text | Low |
| 9 | Abuse / scraping | Medium | Low | Consent gate, session tokens, rate limiting, audit log | Low |
| 10 | User believes PlainMed gives medical advice | Medium | **High** | Disclaimers on every screen; forbidden-claim validation blocks diagnostic and reassurance language | Medium |

### The two risks worth arguing about

**Risk 4 is the most likely failure in practice.** Every guarantee in this
document survives only while nobody installs an error tracker or APM agent
that captures request bodies. The PHI log filter cannot stop an SDK added
later. Recommended control: a written engineering policy plus a CI check
that fails the build if a telemetry dependency appears in the lockfile.
**[Not yet implemented — assign an owner.]**

**Risks 5, 6 and 10 are product risks, not privacy risks**, and they are the
ones most likely to hurt a person. The mitigations are real (a user must
confirm every value before anything is explained, and the validator refuses
to emit diagnostic or reassuring language), but no mitigation prevents a
patient misunderstanding a correct explanation. This is the residual risk
that most needs clinician input before launch.

## 4. Consultation

- [ ] Data Protection Officer: [NAME, DATE]
- [ ] Clinical advisor: [NAME, DATE] — required; the glossary and safety
      wording have had no clinical review
- [ ] Legal counsel: [NAME, DATE]
- [ ] Security reviewer / penetration test: [FIRM, DATE]
- [ ] Representative users consulted (Art. 35(9)): [DATE, METHOD]

## 5. Outcome

- [ ] Residual risks accepted by: [NAME, ROLE, DATE]
- [ ] Prior consultation with supervisory authority required? [YES / NO —
      required if residual high risk remains after mitigation, Art. 36]
- [ ] Review date: [DATE — at minimum on any material change to processing]
