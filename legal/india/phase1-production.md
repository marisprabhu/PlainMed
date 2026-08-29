# Phase 1 for India — from prototype to production

Replaces the HIPAA/GDPR Phase 1 in [LAUNCH.md](../../LAUNCH.md). Ordered so
the long-lead items start first.

**The good news:** India is a cheaper compliance path than the US or EU.
There is no BAA regime to negotiate, health data carries no special-category
burden, cross-border transfer is permissive, and hard enforcement is not
until May 2027.

**The two things that will actually cost you:** the CDSCO classification
opinion, and translation of the notice into the languages your users
actually read.

---

## Week 1 — Entity and appointments

- [ ] **Confirm the Indian legal entity** that will be the Data Fiduciary.
      Everything else names it.
- [ ] **Appoint and publish a Grievance Officer.** Required by s.8(10), and
      the app enforces it: in production the notice endpoint returns 503
      unless `PLAINMED_GRIEVANCE_NAME` and `PLAINMED_GRIEVANCE_EMAIL` are
      set, so a placeholder cannot reach a patient.
- [ ] **Assess Significant Data Fiduciary likelihood.** Model the user
      numbers that would trigger designation; the added obligations (DPO
      resident in India, independent data audit, algorithmic due diligence)
      change your cost base.
- [ ] **Engage Indian counsel** with data-protection *and* medical-device
      experience. These are often different people — you need both.

---

## Weeks 1–6 — CDSCO classification (start immediately; longest lead)

This is the item most likely to delay launch, and the one with the largest
consequence if it goes the wrong way.

- [ ] **Commission a written classification opinion** on whether PlainMed is
      Software as a Medical Device under the Medical Devices Rules 2017 and
      CDSCO's October 2025 software guidance.
- [ ] **Give counsel the specific evidence**, not a product description:
      - `src/plainmed/safety.py` — the forbidden-claim patterns
      - `src/plainmed/pipeline/validate.py` — how they are enforced
      - `tests/test_validate.py` — proof that diagnostic, treatment and
        reassurance language is rejected
      - Sample outputs from `python scripts/offline_check.py`
- [ ] **Record the boundary they draw**, and put it somewhere engineers will
      see it. The validator is what keeps PlainMed on the non-device side;
      after this opinion, changes to it are regulatory changes.
- [ ] **If the opinion says SaMD:** stop. Licensing changes the timeline
      from weeks to many months, and the product needs rescoping first.

---

## Weeks 2–4 — Notice, consent, and language

Mostly built. What remains is content and translation.

- [ ] **Counsel reviews the notice text** at `src/plainmed/compliance/notice.py`
      against Rule 3. It is already itemised, standalone, and plain-language;
      confirm the wording.
- [ ] **Decide which Eighth Schedule languages you ship.** English and Hindi
      exist. Add the languages your actual users read — Tamil, Telugu,
      Bengali, Marathi, Gujarati are the usual next tier.
- [ ] **Commission professional translation.** Not machine translation: a
      mistranslated consent notice is an invalid consent, and this is health
      content.
- [ ] **Bump `CONSENT_VERSION`** in `src/plainmed/api/security.py` to the
      approval date once counsel signs off. Users are then required to accept
      the approved version.

---

## Weeks 2–5 — Clinical review (parallel)

Unchanged by jurisdiction, and still outstanding since v1.

- [ ] **A registered Indian medical practitioner reviews the 40-term
      glossary.** It is the only place PlainMed asserts medical meaning in
      its own voice, and no clinician has read it.
- [ ] **Review against Indian lab conventions.** Reference ranges, units and
      report layouts differ from the synthetic samples — Indian labs
      commonly report in different units for several analytes.
- [ ] **Test on 20–30 real Indian lab report formats** (Dr Lal PathLabs,
      SRL, Metropolis, Thyrocare and hospital labs all differ). This is
      also OCR testing: the layout reconstruction has only been tested on
      synthetic reports.
- [ ] **Record the sign-off.**

---

## Weeks 3–5 — Engineering for production

- [ ] **Set production configuration:**

      ```
      PLAINMED_ENV=production
      PLAINMED_SECRET_KEY=<python -c "import secrets;print(secrets.token_urlsafe(32))">
      PLAINMED_GRIEVANCE_NAME=<published officer>
      PLAINMED_GRIEVANCE_EMAIL=<monitored inbox>
      PLAINMED_MODEL_TIER_TOKEN=<if two-tier>
      ```

- [ ] **Choose hosting region.** Transfer is permissive, but Indian users on
      Indian infrastructure means lower latency and a much simpler answer if
      localisation rules tighten or you become an SDF. Mumbai or Hyderabad.
- [ ] **Run the GPU benchmark** — still unmeasured:

      ```
      PLAINMED_BACKEND=medgemma python scripts/benchmark_model.py
      PLAINMED_QUANTIZATION=4bit python scripts/benchmark_model.py
      ```

- [ ] **Add the telemetry CI check.** DPDP risk equivalent of the DPIA's
      risk #4: an error tracker capturing request bodies would silently
      break every retention claim. Still a policy, not a control.
- [ ] **Wire all four checks into CI:**

      ```
      python -m pytest
      python scripts/offline_check.py
      python scripts/retention_check.py
      python scripts/deident_check.py
      ```

- [ ] **TLS 1.2+ with HSTS**; never expose port 8000 directly.
- [ ] **Redis-backed rate limiting** if more than one replica.
- [ ] **Confirm your log provider is not capturing request bodies.**

---

## Weeks 5–7 — Pre-launch

- [ ] **Third-party penetration test**; fix findings; get a retest letter.
- [ ] **Update the incident runbook for DPDP** breach-notification timings —
      the current draft carries GDPR's 72 hours and HIPAA's 60 days, neither
      of which is the Indian rule.
- [ ] **Rehearse the runbook** as a tabletop exercise.
- [ ] **Publish** the notice, terms, and grievance contact.
- [ ] **Closed beta**, 20–50 users, real Indian reports, in the languages you
      shipped.
- [ ] **Support channel**, treated as a personal-data channel — users will
      paste report contents into it.

---

## Launch gates

Do not launch until all five are true:

1. Written CDSCO classification opinion says PlainMed is not a medical
   device, and engineering knows which changes would alter that.
2. Counsel has approved the notice and terms; both are published.
3. Grievance Officer is appointed, published, and reachable.
4. An Indian clinician has signed off the glossary and safety wording
   against Indian lab conventions.
5. All four automated checks pass in CI, and you have real GPU numbers.

Gate 5 is days of work. Gates 1–4 are weeks, and are not yours to control.

---

## Consent Manager — a decision for later, not now

From **13 November 2026**, DPDP's Consent Manager framework (Rule 4) becomes
operational: registered intermediaries through which data principals can
give, review and withdraw consent across fiduciaries.

Registration is not mandatory for you as a Data Fiduciary, but you may need
to *accept* consent from registered Consent Managers. Put a calendar
reminder for Q3 2026 and ask counsel then. Do not build for it now — the
ecosystem does not exist yet.

---

## Sources

- [India DPDP compliance timeline 2026–27 — India Briefing](https://www.india-briefing.com/news/india-dpdp-compliance-timeline-enforcement-2026-27-44740.html/)
- [DPDP Rules 2025 compliance guide — Seclore](https://www.seclore.com/fundamentals/dpdp-rules-2025-compliance-guide/)
- [Children's data protection under India's DPDP Rules — King Stubb & Kasiva](https://ksandk.com/data-protection-and-data-privacy/childrens-data-protection-under-indias-dpdp-rules/)
- [India's DPDP Rules: cross-border data transfers explained — MediaNama](https://www.medianama.com/2025/11/223-dpdp-rules-cross-border-data-transfers/)
- [Medical device as software: has CDSCO guidance changed the rules? — Cyril Amarchand](https://corporate.cyrilamarchandblogs.com/2026/01/medical-device-as-software-has-cdsco-guidance-changed-the-rules/)
- [SaMD regulation in India: CDSCO classification — Freyr](https://www.freyrsolutions.com/blog/samd-regulation-in-india-cdsco-classification-class-a-d-registration-requirements-emerging-market-strategy)
