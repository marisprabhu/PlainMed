# Incident response runbook

> **DRAFT.** Complete the contacts, then rehearse it. An untested runbook is
> a document, not a control.

## Notification deadlines — the clock starts at awareness

| Regime | Who | Deadline |
|---|---|---|
| GDPR / UK GDPR | Supervisory authority (ICO or lead SA) | **72 hours** from becoming aware |
| GDPR / UK GDPR | Affected individuals | Without undue delay, if high risk to their rights |
| HIPAA | Affected individuals | **60 days** from discovery |
| HIPAA | HHS OCR | 60 days if 500 or more individuals; annually otherwise |
| HIPAA | Media | 60 days if 500 or more in one state or jurisdiction |

"Aware" is earlier than "we finished investigating". Start the clock at the
first credible indication.

## Roles

| Role | Person | Contact |
|---|---|---|
| Incident lead | [NAME] | [PHONE] |
| Security officer (HIPAA) | [NAME] | [PHONE] |
| DPO / privacy lead | [NAME] | [PHONE] |
| Legal counsel | [FIRM] | [PHONE] |
| Cyber insurer | [INSURER, POLICY #] | [24H LINE] |
| Communications | [NAME] | [PHONE] |

## Severity

- **SEV-1 — confirmed or suspected PHI disclosure.** Report content left the
  trusted boundary, was persisted, or was accessed without authorisation.
  Notification clocks start.
- **SEV-2 — control failure with no known disclosure.** For example
  `retention_check.py` failing in production, or a telemetry SDK found
  capturing request bodies. Treat as SEV-1 until you can show no disclosure
  occurred.
- **SEV-3 — availability only.** No PHI implication.

## First hour (SEV-1 / SEV-2)

1. **Preserve evidence before remediating.** Snapshot logs and host state.
   Do not redeploy over the evidence.
2. **Contain.** Take the affected tier out of rotation. The deterministic
   backend still serves validated explanations without a GPU, so degrading
   is preferable to going dark — unless the trusted tier itself is
   compromised, in which case stop serving entirely.
3. **Notify the incident lead and counsel.** Counsel early: their advice may
   be privileged, and it shapes what you write down next.
4. **Open a written timeline** and keep it contemporaneously.

## Investigation — the questions that decide notification

- What data was involved: photos, OCR text, or de-identified values only?
  De-identified values crossing the model boundary are not PHI, and that
  distinction may determine whether notification is required at all.
- How many individuals? The 500 threshold changes HIPAA obligations.
- Was the data accessed, or only exposed?
- Is it still exposed?

## PlainMed-specific tripwires

Each of these means a control has failed. Treat as SEV-2 minimum:

- `retention_check.py` or `deident_check.py` failing outside development.
- A `DeidentificationError` in production. The system refused to forward the
  text, which is the safe outcome, but it means construction let something
  through and needs investigating.
- Any file appearing in the container filesystem at runtime — the root
  filesystem should be read-only.
- A new dependency that transmits data off-host.

## After

- [ ] Written post-incident review within [N] days
- [ ] Root cause identified and fixed
- [ ] A regression test added — a control that failed silently once will
      fail silently again
- [ ] DPIA and this runbook updated
