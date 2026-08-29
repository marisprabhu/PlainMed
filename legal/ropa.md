# Record of Processing Activities (GDPR Art. 30)

> **DRAFT.** Required because you process special-category data. Complete
> the organisational fields; the processing descriptions below match the
> system as built.

**Controller:** [LEGAL ENTITY], [ADDRESS], [CONTACT]
**DPO:** [NAME, or "not appointed — assess Art. 37"]
**EU/UK representative:** [IF APPLICABLE]
**Last updated:** [DATE]

## Activity 1 — Explaining a laboratory report

| Field | Entry |
|---|---|
| Purpose | Producing a plain-language, source-linked explanation of a report the user supplies |
| Categories of data subject | Adults using the service for their own report, or one they are authorised to act for |
| Categories of personal data | Health data (lab results); incidental identifiers appearing on the uploaded document |
| Special category | Yes — Art. 9(1) health data |
| Lawful basis | Art. 6(1)(a) consent; Art. 9(2)(a) explicit consent |
| Recipients | [CLOUD HOST] (trusted tier); [GPU PROVIDER] (de-identified values only) |
| Third-country transfers | [COUNTRIES + MECHANISM] |
| Retention | Duration of the request only; not stored |
| Security measures | TLS in transit; no persistence; PHI excluded from logs; de-identification before model processing; consent gate; rate limiting; audit logging. Verified by automated checks in CI |

## Activity 2 — Service integrity and abuse prevention

| Field | Entry |
|---|---|
| Purpose | Preventing abuse, maintaining availability, meeting audit-control obligations |
| Categories of personal data | Anonymous session identifier, IP address (transient, for rate limiting), timestamps |
| Special category | No |
| Lawful basis | Art. 6(1)(f) legitimate interests; Art. 6(1)(c) where an audit obligation applies |
| Recipients | [LOG PROVIDER] |
| Retention | [PERIOD — recommend 6 years where HIPAA §164.316(b)(2) applies] |
| Security measures | Records contain no report content and no direct identifiers |

## Activity 3 — Consent records

| Field | Entry |
|---|---|
| Purpose | Evidencing that a user accepted the current terms before processing |
| Categories of personal data | Anonymous session identifier, consent version, timestamp |
| Lawful basis | Art. 6(1)(c) legal obligation (accountability, Art. 5(2)) |
| Retention | [PERIOD] |
| Limitation | Because no account exists, consent is evidenced against an anonymous session rather than a named individual. This is a deliberate consequence of the privacy design and is disclosed in the privacy notice |
