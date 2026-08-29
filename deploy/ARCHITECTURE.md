# Two-tier deployment: cheap GPU without handling PHI on it

## The constraint that shapes everything

Commodity GPU marketplaces are cheap — an RTX A4000 (16 GB) runs about
**$0.17/hr** and an L4 (24 GB) about **$0.39–0.44/hr** on RunPod, versus
several times that on a hyperscaler. But those community tiers **will not
sign a BAA**, which normally rules them out for anything touching PHI.

PlainMed avoids the conflict rather than accepting it: the GPU never
receives identifiable data.

## The split

```
                 photo (PHI, TLS)
                        │
        ┌───────────────▼────────────────┐
        │  TRUSTED TIER                  │   BAA required
        │  CPU only — no GPU needed      │   ~$0.02–0.05/hr
        │                                │
        │  decode → OCR → parse          │
        │  → DE-IDENTIFY                 │
        └───────────────┬────────────────┘
                        │  "Glucose 108 mg/dL (ref 70-99) [H]"
                        │  verified free of 14 identifier categories
        ┌───────────────▼────────────────┐
        │  MODEL TIER                    │   no BAA needed
        │  commodity GPU                 │   ~$0.17–0.44/hr
        │                                │
        │  MedGemma → narrative          │
        └───────────────┬────────────────┘
                        │  statements + span IDs
        ┌───────────────▼────────────────┐
        │  TRUSTED TIER                  │
        │  validate → assemble → return  │
        └────────────────────────────────┘
```

The expensive-to-comply-with tier is the cheap-to-run one (CPU), and the
expensive-to-run tier (GPU) is the one with no compliance burden. That
inversion is the whole point.

Enforced by `scripts/deident_check.py`, which runs in CI. If it fails, this
architecture is void and the GPU provider needs a BAA.

## Caveats you must not skip

**OCR placement.** PaddleOCR on GPU is more accurate on lab tables, but OCR
input *is* the photo, which is PHI. So either:

- **(a)** Run OCR on the trusted tier — CPU (RapidOCR, ~1.8 s/report
  measured) or a BAA-covered GPU. Slower or dearer, but simple.
- **(b)** Put OCR on a BAA-covered GPU and MedGemma on the cheap one. Two
  GPU pools, more complexity, but each is right-sized.

**Do not** run OCR on the commodity GPU. That would put PHI on an uncovered
host and collapse the whole argument. Configuration for the split is in
`docker-compose.tiers.yml`.

**Single-host deployment gets you nothing.** If both tiers run in one
container, the host handles PHI and needs a BAA regardless of the internal
boundary. The boundary only buys you something when the tiers are separated.

## Choosing a GPU

MedGemma 1.5 4B, approximate weight sizes:

| Precision | Weights | Plus KV cache | Smallest sensible card |
|---|---|---|---|
| bf16/fp16 (`auto`) | ~8–9 GB | ~10–12 GB | L4 24 GB |
| 8-bit | ~4.5 GB | ~6–8 GB | A4000 16 GB |
| 4-bit NF4 | ~2.5–3 GB | ~4–6 GB | A4000 16 GB, comfortably |

Set with `PLAINMED_QUANTIZATION=auto|8bit|4bit`.

**These are estimates from parameter count, not measurements.** Run
`scripts/benchmark_model.py` on your GPU and use its numbers. It reports
latency, peak memory, and — the one people forget — the share of generated
statements the validator rejects, which is how you detect a quantization
level that has degraded quality past usefulness.

Note that T4 (16 GB, Turing) lacks bf16 support and needs fp16; it is cheap
but slow for this. L4 is usually the better value once throughput matters.

## Cost model

You cannot price this yet, because the input is unmeasured. The shape:

```
cost per report = GPU $/hr ÷ 3600 × GPU-seconds per report
```

With A4000 at $0.17/hr:

| GPU-seconds/report | Cost/report | Reports per $1 |
|---|---|---|
| 2 s | $0.000094 | ~10,600 |
| 5 s | $0.000236 | ~4,200 |
| 15 s | $0.000708 | ~1,400 |

Even the pessimistic row is a fraction of a cent, so **GPU cost is unlikely
to be your constraint** — idle capacity is. A warm GPU costs the same
whether it serves one report or a thousand, so utilisation dominates:

- Scale-to-zero saves money but adds a cold start of a minute or more
  (model load dominates, which is why the healthcheck allows 180 s).
- A warm pool costs ~$122/month per always-on A4000 at $0.17/hr.
- The deterministic backend needs no GPU at all, so you can serve validated
  explanations during a GPU outage or capacity crunch rather than failing.

**Measure before pricing:** GPU-seconds per report, and concurrent reports
per GPU at acceptable latency. Those two numbers, plus your expected
concurrency, determine instance count. Nothing else in this document is a
substitute for them.

## Prices verified August 2026

RunPod: A4000 16 GB ~$0.17/hr (Community), L4 24 GB ~$0.39–0.44/hr. Secure
Cloud is often close to double Community. Billing is per second.
Re-check before committing — GPU pricing moves fast.

Sources:
- [RunPod GPU Pricing — GPUPerHour](https://gpuperhour.com/providers/runpod)
- [RunPod Pricing 2026 — Flexprice](https://flexprice.io/blog/runprod-pricing-guide-with-gpu-costs)
- [AI Business Associate Agreements 2026 — The AI Career Lab](https://theaicareerlab.com/blog/ai-business-associate-agreements-baa-vendor-guide-2026)
- [Can I Use GPU Cloud for HIPAA Workloads? — io.net](https://io.net/p/f-2)
