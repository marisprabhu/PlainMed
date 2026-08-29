# Legal and compliance pack

**These are drafts prepared for review by qualified counsel. They are not
legal advice, and none of them should be published or relied on until a
lawyer admitted in your target market has reviewed and approved them.**

The point of this folder is to make the lawyer's job small and cheap. A
solicitor handed "we built a health app, please advise" bills for discovery.
A solicitor handed an accurate data-flow map, a completed processing record,
and a first-draft policy that already matches what the code does, bills for
review. The documents here are written to be *accurate about the system as
built* — that accuracy is the part an engineer can contribute and a lawyer
cannot.

## What is in here

| File | What it is | Who finishes it |
|---|---|---|
| [data-flow.md](data-flow.md) | Exactly what data exists, where it goes, how long it lives | Engineering (done) — lawyer reads it |
| [ropa.md](ropa.md) | GDPR Art. 30 Record of Processing Activities | Draft; you complete the org details |
| [dpia.md](dpia.md) | GDPR Art. 35 Data Protection Impact Assessment | Draft; requires DPO/counsel sign-off |
| [privacy-notice.md](privacy-notice.md) | User-facing privacy notice | Draft; counsel must approve before publishing |
| [terms.md](terms.md) | User-facing terms of service | Draft; counsel must approve before publishing |
| [subprocessors.md](subprocessors.md) | Vendor list and BAA/DPA tracker | You fill in as you choose vendors |
| [incident-response.md](incident-response.md) | Breach detection and notification runbook | Draft; needs your contact details and legal review |
| [security-controls.md](security-controls.md) | HIPAA Security Rule control mapping | Engineering draft; auditor reviews |

## The honest status

**What the code now does** (verified by tests, and by
`scripts/retention_check.py` and `scripts/deident_check.py`):

- No report content is written to disk or to logs.
- Identifiers are removed before any AI model sees the report.
- Nothing is processed without an explicit consent step.
- Every request is authenticated, rate-limited, and audit-logged without
  identifying the user.

**What is still missing before a real patient may use this.** None of these
can be closed by writing code:

1. **Signed BAAs** with every vendor that could touch PHI — cloud host, GPU
   provider, log aggregator, error tracker, email provider. Unsigned means
   unlawful, not merely risky.
2. **Counsel review** of every document in this folder.
3. **Regulatory classification.** An app that explains a report without
   diagnosing is *usually* outside medical-device regulation (FDA in the US,
   UKCA/MDR in the UK/EU). "Usually" is not a legal opinion, and the answer
   differs per market. Get a written one before launch — and re-open it if
   you ever add triage, risk scoring, or anything a user could read as
   advice.
4. **Clinician review** of the 40-term glossary and all safety wording.
5. **Penetration test** by a third party.
6. **Cyber liability and professional indemnity insurance.**
7. **A named accountable person** — a Data Protection Officer if GDPR
   Art. 37 applies to you, and a HIPAA Security Officer if you handle US PHI.

## Market: India

The target market is **India first**. See
[india/README.md](india/README.md) for what changes under the DPDP Act and
CDSCO, and [india/phase1-production.md](india/phase1-production.md) for the
ordered path to production.

The documents in this folder are HIPAA/GDPR-framed and remain useful for a
later US or EU launch. The India README says which to reuse, which to
replace, and which do not apply.

## The decision that remains

**Which Eighth Schedule languages to ship.** DPDP requires the notice to be
available in English or an Indian language, and a patient who cannot read
the notice cannot consent to it. English and Hindi are implemented; the rest
is a market decision requiring professional translation.

(The children's-data question is settled: DPDP defines a child as anyone
under 18 and requires verifiable parental consent, so PlainMed excludes
under-18s and enforces it in code.)
