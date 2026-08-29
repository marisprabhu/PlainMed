# Privacy Notice — PlainMed

> **DRAFT — NOT FOR PUBLICATION.** Counsel must review and approve before
> this is shown to any user. Placeholders in `[BRACKETS]` must be completed.
> Every factual claim below matches the system as built (see
> [data-flow.md](data-flow.md)); if the code changes, this must change too.

**Last updated: [DATE] · Version: 2026-08-28**

## The short version

- Your report is used to produce your explanation, and then it is gone.
- We do not store it. We do not have an account for you. We cannot look up
  what you scanned, because there is nothing to look up.
- Before any AI model sees your report, we remove identifying details such
  as your name, date of birth, and record numbers.
- We do not sell your data, run advertising, or share your report with
  anyone.

The rest of this notice is the detail behind those four statements.

## Who we are

[LEGAL ENTITY NAME], [REGISTERED ADDRESS], [COMPANY NUMBER] is the data
controller. Contact: [PRIVACY EMAIL]. [If applicable: our Data Protection
Officer is [NAME], reachable at [DPO EMAIL].]

## What we process, and why

| What | Why | Lawful basis (GDPR) |
|---|---|---|
| The photo, PDF, or text of your report | To read the values and produce your explanation | Explicit consent, Art. 9(2)(a) |
| Corrections you make on the review screen | To correct what we misread | Explicit consent, Art. 9(2)(a) |
| An anonymous session identifier | To prevent abuse and keep the service available | Legitimate interests, Art. 6(1)(f) |
| Your acceptance of these terms | To evidence that you consented | Legal obligation, Art. 6(1)(c) |

Health data is a special category under GDPR Art. 9. We rely on your
explicit consent, which is why nothing happens until you tap through the
consent step, and why you can withdraw at any time by closing the page.

## How long we keep it

**Your report: for the duration of the request only.** Typically a few
seconds. It is held in memory, never written to disk, and never written to
a log. It is discarded when your explanation is returned.

**Anonymous audit records: [RETENTION PERIOD — recommend 6 years for HIPAA
§164.316(b)(2)].** These record that a session used a feature at a time, and
whether it succeeded. They contain no report content and nothing that
identifies you.

## Who we share it with

No one, for the report itself. The following vendors support the service and
are contractually bound to protect it — the current list is at
[SUBPROCESSORS URL]:

| Vendor | Role | Sees report content? |
|---|---|---|
| [CLOUD HOST] | Runs the trusted tier | Yes — covered by [BAA / DPA] |
| [GPU PROVIDER] | Runs the AI model | No — receives de-identified values only |
| [LOG PROVIDER] | Stores audit records | No |

We do not sell personal data. We do not use it for advertising. We do not
use your report to train AI models.

## The de-identification step

Before your report reaches the AI model, we rebuild it as a list of test
results — the test name, the number, the unit, the range, and any flag your
lab added. Your name, date of birth, record number, address, and the
ordering doctor's name are not included.

We do this by *rebuilding* rather than *deleting*: the model only ever
receives fields we recognised as test results, so information we did not
recognise is withheld rather than passed along. [COUNSEL: confirm the
characterisation of this as de-identification is one you are comfortable
publishing.]

## Your rights

Under GDPR you may request access to, correction of, deletion of, or a copy
of your personal data, and you may object to processing or complain to a
supervisory authority ([ICO / relevant authority]).

**An honest limitation:** because we store nothing about your report and
have no account for you, we usually cannot act on an access or deletion
request — there is nothing on file to retrieve or erase. This is a
consequence of the privacy design, not an evasion. If you believe we hold
something about you, contact [PRIVACY EMAIL] and we will investigate.

## Security

Data is encrypted in transit (TLS 1.2+). The application writes no report
data to disk or logs, and this is verified automatically before each
release. Access to production systems is restricted and logged.

We cannot promise perfect security, and we do not claim that data in memory
during processing is protected against every possible attack on the
underlying infrastructure.

## Children

PlainMed is not intended for anyone under 18. We do not knowingly process
data from children. [COUNSEL: confirm; if the age limit changes, COPPA
(US) and GDPR Art. 8 obligations may apply.]

## International transfers

[COMPLETE: name the countries data is processed in, and the transfer
mechanism — adequacy decision, Standard Contractual Clauses, or UK IDTA.]

## Changes

If we change this notice materially we will ask you to accept the new
version before you next use PlainMed. The version identifier at the top of
this page is checked by the app.

## Not medical advice

PlainMed explains what your report says. It does not diagnose, does not
recommend treatment, and is not a substitute for a qualified clinician.
Always confirm your interpretation with your doctor.
