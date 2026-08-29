# Deploying PlainMed

Cloud GPU inference with zero retention. This document covers what the code
guarantees, what it cannot, and what you must add before real patients use it.

## What the application guarantees

Verified by `python scripts/retention_check.py`, which drives a real request
through the app and then asserts from the outside:

| Property | Enforcement |
|---|---|
| No report data written to disk | No file writes in the request path; the check fails if any file appears |
| No report data in logs | `PhiLogFilter` on the root logger drops records carrying report fields; handlers log counts only |
| No caching by browsers or proxies | `no-store` on every response |
| No inference leaves your infrastructure | Weights loaded `local_files_only`; `HF_HUB_OFFLINE=1` set before transformers imports |
| Explanations traceable to the report | Citation, number, and forbidden-claim validation on every sentence |

Run it in CI. It is the difference between a claim and a control.

## What the application does NOT guarantee

State these plainly in your privacy policy rather than letting a customer
infer more than is true:

- **Memory is not scrubbed.** Report text exists in process memory while a
  request is handled. A host compromise or a core dump could expose it.
- **The host is not hardened by this repo.** Disk encryption, network policy,
  patching, and access control are yours.
- **TLS is terminated upstream.** Run this behind a load balancer with TLS
  1.2+; never expose port 8000 directly.
- **No authentication is built in.** Anyone who can reach the API can use it.
  Add auth at the gateway before exposing it publicly.
- **Uploads are not scanned** for malicious payloads beyond image decoding.

## Before real patient data

This is the gap between the current prototype and a lawful service.

1. **Legal basis.** HIPAA (US) needs a signed BAA with every processor
   touching PHI — cloud provider, GPU host, log aggregator, error tracker.
   GDPR (EU/UK) needs a lawful basis, a DPIA (health data is special
   category), and a data-residency decision.
2. **Region pinning.** Run GPUs in the region matching the user's
   jurisdiction. Do not let a request fail over across a border.
3. **Turn off third-party telemetry.** Error trackers and APM agents capture
   request bodies by default. Either disable body capture or do not install
   them. This is the most common way a zero-retention claim quietly becomes
   false.
4. **Authentication and rate limiting** at the gateway, per-IP and per-account.
5. **Penetration test and a documented incident-response plan**, including
   breach notification timelines (72 hours under GDPR).
6. **Clinician review** of the glossary and all safety wording.
7. **Regulatory classification.** An app that explains a report without
   diagnosing is usually not a medical device — but "usually" is not a legal
   opinion. Get one for each market before launch. Adding anything that reads
   as diagnosis or triage changes the answer.

## Model weights

MedGemma is gated under Google's Health AI Developer Foundations terms,
separate from this application's licence. Download once on the host:

```bash
python scripts/download_model.py
```

Mount them read-only (`../models:/models:ro`). Do not bake weights into an
image you push to a shared registry.

## Running

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Then open http://127.0.0.1:8000.

## Scaling

- **One worker per GPU.** Workers cannot share a device safely; scale with
  replicas, each with its own GPU, not with `--workers`.
- **Warmup is slow, requests are fast.** Model load dominates cold start,
  which is why `HEALTHCHECK` has a 180 s start period. Keep a warm pool;
  scale-to-zero will produce minute-long first requests.
- **OCR and the LLM share a GPU.** A scan is one accelerator, not two. Watch
  peak memory when both are resident before sizing instances.
- **The deterministic backend needs no GPU.** If model capacity runs out,
  the service degrades to validated template summaries rather than failing.

## Cost note

GPU hours are the dominant cost and scale with concurrent users, not
registered users. Before pricing anything, measure: tokens per report, seconds
of GPU per report, and how many concurrent reports one GPU sustains at
acceptable latency. Those three numbers determine whether the unit economics
work. None of them are measured yet.
