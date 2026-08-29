# India compliance — DPDP, CDSCO, and what changes

> **Drafts for Indian counsel.** Not legal advice. The engineering facts are
> accurate about the system as built; the legal conclusions are for a lawyer
> admitted in India to reach.

Launching in India rather than the US or EU changes the framework
substantially — mostly in your favour, with two exceptions that cost real
work.

## The regime, and the timeline you are launching into

The **Digital Personal Data Protection Act 2023** is operative: the **DPDP
Rules 2025 were notified on 13 November 2025** (G.S.R. 846(E)) with a phased
commencement.

| Date | What takes effect |
|---|---|
| 13 Nov 2025 | Definitions; Data Protection Board constituted |
| 13 Nov 2026 | Board may inquire and levy penalties; Consent Manager registration opens |
| **13 May 2027** | Notice, consent, data principal rights, retention, transfer and breach obligations apply in full |

You are launching into a **soft-enforcement window**, with hard enforcement
from May 2027. That is a genuine runway — but it is not permission to defer.
Retrofitting consent architecture into a live product with users is far more
expensive than building it now, which is why the consent flow already exists
in code.

Maximum penalty is **₹250 crore** per instance for failing to take
reasonable security safeguards.

## Five differences from the GDPR/HIPAA pack

**1. Health data has no special category.** GDPR Art. 9 singles out health
data; DPDP does not. All personal data is treated alike. This does *not*
mean lab reports are low-risk — sensitivity feeds into whether you are
designated a Significant Data Fiduciary, and reputational exposure is
unchanged. But the extra legal machinery GDPR imposes on health data does
not apply, which removes a layer of work.

**2. A child is anyone under 18, and consent must be *verifiable*.** This is
stricter than GDPR (13–16 depending on member state). Rule 10 contemplates
verification through DigiLocker or equivalent identity infrastructure.
Building verifiable parental consent is a substantial project, so **PlainMed
excludes under-18s instead** — and the exclusion is enforced in code, not
merely stated in the terms:

- The consent screen requires a separate age affirmation.
- The API returns 403 without it and records `denied_age` in the audit log.
- The session token carries an `adult` claim; a token without it is rejected.

Tracking, behavioural monitoring, and targeted advertising to children are
prohibited outright. PlainMed does none of these for anyone.

**3. Cross-border transfer is a blacklist, not a whitelist.** Under s.16 and
Rule 15, personal data may be transferred anywhere *except* countries the
Central Government restricts. This is far more permissive than GDPR's
adequacy/SCC regime — **the cheap foreign GPU is legally easier in India
than it would be in Europe.**

Two cautions. Sector-specific rules may still impose localisation, and if
you are designated a Significant Data Fiduciary, Rule 12(4) allows the
government to restrict specified categories from leaving India. Design so
that moving inference onshore is a configuration change, not a rewrite — the
tiering already allows this.

**4. Notice is a document, not a link.** Rule 3 requires standalone notice
in clear plain language, itemising each category of personal data against
its specific purpose, presented independently of anything else. A footer
link to a privacy policy does not satisfy it. Implemented at
`GET /api/v1/notice`, rendered as the first screen.

**5. The notice must be available in English or an Eighth Schedule
language.** This is a product requirement, not a footnote: a patient who
cannot read the notice cannot consent to it. English and Hindi ship;
`src/plainmed/compliance/notice.py` takes further languages without code
changes. **Which languages you ship is a market decision you need to
make** — Tamil, Telugu, Bengali, Marathi and Gujarati are the usual next
tier, and each needs professional translation, not machine translation.

## What DPDP requires, and where it lives

| Obligation | Where |
|---|---|
| Itemised notice before processing (Rule 3) | `GET /api/v1/notice`; first screen in the app |
| Notice in an Eighth Schedule language | `compliance/notice.py` — English + Hindi |
| Free, specific, informed, unambiguous consent (s.6) | Two separate affirmations; no pre-ticked boxes |
| Withdrawal as easy as giving (s.6(4)) | "Withdraw consent" button; clears the session and both affirmations |
| Verifiable parental consent for under-18s (s.9) | Avoided by excluding under-18s, enforced server-side |
| Purpose limitation and data minimisation (s.6(1)) | Only the report is processed; de-identified before the model |
| Erase when purpose is served (s.8(7)) | Nothing is stored — `retention_check.py` proves it |
| Reasonable security safeguards (s.8(5)) | TLS, no persistence, no PHI in logs, rate limiting, audit log |
| Grievance redressal, published contact (s.8(10)) | `PLAINMED_GRIEVANCE_NAME` / `_EMAIL`; production refuses to serve notice without them |
| Breach notification to Board and each affected principal | [incident-response.md](../incident-response.md) — **timings need updating for DPDP** |
| Data principal rights, incl. nomination (s.14) | Described in the notice; see the limitation below |

**An honest limitation to disclose, not paper over.** Because nothing is
stored and there are no accounts, an access or erasure request usually has
nothing to act on. That is a consequence of the privacy design, and the
notice says so plainly. Confirm with counsel that this characterisation is
one they are comfortable publishing.

## CDSCO — the classification that decides everything

The **Medical Device Rules 2017** and CDSCO's **draft guidance on Medical
Device Software (21 October 2025)** apply a four-tier risk classification
(Class A–D). Software performing **disease screening, clinical decision
support, or patient monitoring** requires licensing before it may be
marketed in India.

PlainMed is designed to fall outside that. It:

- describes what a document the patient already holds says;
- does not diagnose, screen, triage, or score risk;
- does not support a clinician's decision — it is patient-facing;
- refuses to emit diagnostic, treatment, or reassurance language.

**The forbidden-claim validator is therefore a regulatory control, not only
a safety feature.** It is the technical mechanism keeping the product on the
non-device side of the line. Weakening it — adding "your result suggests…",
a risk score, or a triage prompt — could reclassify PlainMed as SaMD and
require a CDSCO licence. Treat changes to `plainmed/safety.py` and
`pipeline/validate.py` as regulatory changes, not product tweaks.

**Get this in writing from Indian regulatory counsel before launch.**
"Usually not a device" is not a defence.

## Also check with counsel

- **Telemedicine Practice Guidelines 2020** (NMC/MoHFW) — these govern
  registered medical practitioners providing consultation. PlainMed involves
  no practitioner and gives no advice, so they should not apply. Confirm.
- **ABDM / Health Data Management Policy** — applies if you integrate with
  ABHA or the health-records ecosystem. You do not today. If you ever do,
  this becomes a substantial new workstream.
- **IT Act 2000 s.43A and the SPDI Rules 2011** — largely superseded by
  DPDP for personal data, but confirm the transition position.
- **Consumer Protection Act 2019** and the e-commerce rules — affect the
  terms, disclaimers, and grievance timelines.
- **Significant Data Fiduciary designation** — criteria include volume and
  sensitivity. Model what user numbers would trigger it, because the extra
  obligations (DPO in India, independent audit, algorithmic due diligence)
  are material.

## Documents to adapt

The existing pack is GDPR/HIPAA-framed. For India:

| Document | Action |
|---|---|
| [data-flow.md](../data-flow.md) | Reusable as-is — engineering facts do not change |
| [privacy-notice.md](../privacy-notice.md) | **Replace** with the DPDP notice at `/api/v1/notice` |
| [terms.md](../terms.md) | Rewrite: Indian governing law, Consumer Protection Act, 18+ |
| [dpia.md](../dpia.md) | DPDP has no DPIA requirement unless you are an SDF. Keep it — it is good practice and insurers ask |
| [ropa.md](../ropa.md) | Not required by DPDP. Keep as internal record-keeping |
| [subprocessors.md](../subprocessors.md) | Reframe: BAAs are HIPAA. India needs contractual data-processing terms |
| [incident-response.md](../incident-response.md) | **Update timings** — DPDP breach notification differs from GDPR's 72 hours |
