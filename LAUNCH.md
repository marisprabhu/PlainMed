# Launch runbook

> **Target market is India.** The India-specific Phase 1 — DPDP, CDSCO, and
> the ordered path to production — is at
> [legal/india/phase1-production.md](legal/india/phase1-production.md), and
> supersedes Phase 1 below. The remaining phases still apply; the framework
> references change from HIPAA/GDPR to DPDP.

Ordered sequence to take PlainMed from working prototype to a service real
patients may lawfully use.

**The critical path is legal, not technical.** The software is close to
ready; the agreements and reviews are not, and several of them take weeks of
someone else's calendar time. Start Phase 1 today even though it produces no
visible progress — everything else waits on it.

Timings assume one engineer plus responsive counsel. They are estimates.

---

## Phase 0 — Decide (a few days)

Four decisions that change everything downstream. Get them wrong and Phase 2
gets redone.

- [ ] **Pick one market.** US (HIPAA), UK (UK GDPR + DPA 2018), and EU (GDPR)
      have materially different rules. One market done properly is far
      cheaper and faster than three done partially. Expand later.
- [ ] **Confirm the age floor.** Draft terms say 18+, which avoids COPPA and
      GDPR Art. 8 entirely. Relaxing this later is easy; discovering you
      needed it after launch is not.
- [ ] **Name an accountable person.** A HIPAA Security Officer (US) and/or a
      DPO if GDPR Art. 37 applies. This is a named human, not a role you
      intend to fill.
- [ ] **Choose the tiering.** Two-tier (cheap GPU, per
      [deploy/ARCHITECTURE.md](deploy/ARCHITECTURE.md)) or single-tier on a
      BAA-covered GPU. Two-tier is cheaper to run and more complex to
      operate.

---

## Phase 1 — Legal (4–10 weeks, start now)

Nothing here can be shortened by writing code, and everything in Phase 4
waits on it.

- [ ] **Engage counsel** admitted in your chosen market, with health-data
      experience. Send them [legal/](legal/README.md) as a package — the
      documents are drafted to be accurate about the system as built, which
      turns an open-ended advisory engagement into a review.
- [ ] **Get a written regulatory classification.** Is PlainMed a medical
      device in your market? Explaining without diagnosing is *usually*
      outside FDA / UKCA / MDR scope, but "usually" is not a legal opinion.
      Get it in writing, and re-open it if you ever add triage, risk
      scoring, or anything a user could read as advice.
- [ ] **Sign BAAs / DPAs** with every vendor that could touch PHI. Track in
      [legal/subprocessors.md](legal/subprocessors.md). The one people miss:
      **your CDN or load balancer terminates TLS and therefore sees
      plaintext PHI.** It needs an agreement.
- [ ] **Counsel approves** the privacy notice and terms. Do not publish the
      drafts as-is.
- [ ] **Complete and sign the DPIA** ([legal/dpia.md](legal/dpia.md)),
      including the decision on whether Art. 36 prior consultation is
      required.
- [ ] **Buy insurance** — cyber liability and professional indemnity.
      Brokers will ask for the DPIA and pen-test report, so sequence this
      after those exist.

---

## Phase 2 — Clinical (2–4 weeks, parallel with Phase 1)

The one outstanding item from the very first version, and still the thing
most likely to hurt someone.

- [ ] **Clinician reviews the 40-term glossary.** It is the only place
      PlainMed asserts medical meaning in its own voice. I wrote it; nobody
      clinical has read it.
- [ ] **Clinician reviews all safety wording** — disclaimers, status labels
      ("Marked high in your report", never "Dangerous"), and the clinician
      questions.
- [ ] **Clinician reviews 20–30 real-format reports** end to end, looking
      for explanations that are technically correct but misleading.
- [ ] **Record their sign-off** — it is evidence for the DPIA and for
      insurers.

---

## Phase 3 — Engineering (1–2 weeks)

- [ ] **Provision a GPU box** and run the benchmark. This is the gap that
      has been open since the first deck:

      ```
      pip install -e ".[gpu]" && python scripts/download_model.py
      PLAINMED_BACKEND=medgemma python scripts/benchmark_model.py
      PLAINMED_QUANTIZATION=4bit python scripts/benchmark_model.py
      ```

      Compare the two. If 4-bit pushes the validator rejection rate much
      above ~20%, quality has degraded past usefulness — use 8-bit or a
      bigger card. Record latency, peak VRAM, and rejection rate.
- [ ] **Add a CI check that fails on telemetry dependencies.** This is
      DPIA risk #4 and the single most likely way the privacy guarantees
      silently become false: error trackers and APM agents capture request
      bodies by default, and the PHI log filter cannot stop an SDK added
      later. Currently a policy, not a control. **Assign an owner.**
- [ ] **Wire all four checks into CI** so a regression blocks the build:

      ```
      python -m pytest && python scripts/offline_check.py && \
      python scripts/retention_check.py && python scripts/deident_check.py
      ```
- [ ] **Set production secrets.** The app refuses to start in production
      without a signing key, deliberately — without it sessions break across
      restarts and replicas.

      ```
      python -c "import secrets; print(secrets.token_urlsafe(32))"
      ```

      Set `PLAINMED_SECRET_KEY`, `PLAINMED_ENV=production`, and
      `PLAINMED_MODEL_TIER_TOKEN` if running two tiers.
- [ ] **Replace the in-memory rate limiter with Redis** *if* running more
      than one replica. In-memory limits per replica, so N replicas means N
      times the intended limit.
- [ ] **Put TLS in front** (1.2+, HSTS). Never expose port 8000 directly.
- [ ] **Isolate the model tier** on a private network. It must not be
      reachable from the internet.
- [ ] **Configure log retention** — recommend 6 years where HIPAA
      §164.316(b)(2) applies. Confirm your log provider is not capturing
      request bodies.

---

## Phase 4 — Pre-launch gates (2–3 weeks)

- [ ] **Third-party penetration test.** Fix findings, get a retest letter.
- [ ] **Rehearse the incident runbook**
      ([legal/incident-response.md](legal/incident-response.md)) as a
      tabletop exercise. An untested runbook is a document, not a control.
      The GDPR clock is 72 hours from *awareness*, not from investigation.
- [ ] **Publish the approved** privacy notice and terms, and the
      subprocessor list. Update `CONSENT_VERSION` in
      `src/plainmed/api/security.py` to the publication date — users are
      then required to accept the current version.
- [ ] **Closed beta**, 20–50 users, real reports, explicit consent to
      contact them. Watch for OCR failures on layouts you have not seen.
- [ ] **Set up a support channel** and treat it as a PHI channel — users
      will paste report contents into it regardless of what you tell them.
- [ ] **Confirm the load balancer, WAF, and monitoring** are all covered by
      signed agreements and none capture request bodies.

---

## Phase 5 — Launch

- [ ] Deploy. Keep a warm GPU pool: scale-to-zero produces cold starts over
      a minute because model load dominates.
- [ ] Watch the audit log for `denied_no_consent` and `rate_limited` spikes.
- [ ] Watch for `DeidentificationError` in production. It means the system
      *refused* to forward text — the safe outcome — but construction let
      something through and it needs investigating that day.
- [ ] Have a rollback ready. The deterministic backend needs no GPU, so a
      GPU outage degrades to validated template explanations rather than an
      outage.

---

## Order of magnitude

| | Cost |
|---|---|
| Legal (counsel, classification, doc review) | the largest line item by far |
| Penetration test | one-off, four figures |
| Clinician review | days of a clinician's time |
| Insurance | annual |
| GPU (one warm A4000 @ $0.17/hr) | ~$122/month |
| Trusted tier (CPU) | tens of dollars/month |

GPU is roughly the cheapest thing on this list. At $0.17/hr, even a
pessimistic 15 GPU-seconds per report is about $0.0007 — **GPU cost will not
be your constraint; idle capacity and legal spend will.**

---

## What "done" looks like

Launch when all four are true:

1. Counsel has approved the published documents and given a written
   regulatory classification.
2. Every vendor that can touch PHI has a signed agreement.
3. A clinician has signed off the glossary and safety wording.
4. `pytest`, `offline_check`, `retention_check`, and `deident_check` all
   pass in CI, and you have real GPU numbers from `benchmark_model.py`.

Item 4 is days of work. Items 1–3 are weeks, and they are not yours to
control. That is why Phase 1 starts today.
