# Data flow

Engineering reference, written to be accurate about the system as built. It
is the input to every other document in this folder — if this is wrong, the
DPIA and the privacy notice are wrong too.

Claims marked **[verified]** are enforced by a check that runs in CI.

## Data categories

| Data | Contains identifiers? | Where it exists | Lifetime |
|---|---|---|---|
| Uploaded photo | **Yes** — a report shows name, DOB, MRN | Request memory, trusted tier | Duration of the request |
| OCR text | **Yes** — same content as the photo | Request memory, trusted tier | Duration of the request |
| Parsed values | No — analyte, number, unit, range, flag | Request memory; returned to the client | Duration of the request |
| Model prompt | No — reconstructed values only **[verified]** | Model tier | Duration of the inference |
| Explanation | No — derived from parsed values | Returned to the client | Duration of the request |
| Session token | No — random ID, timestamp, consent version **[verified]** | Client memory | 1 hour |
| Audit log | No — session ID, endpoint, outcome, timing **[verified]** | Log sink | Per retention policy (recommend 6 years for HIPAA) |

## The trust boundary

This is the load-bearing design decision, and the reason a commodity GPU is
usable at all:

```
  Phone
    │  photo (PHI, over TLS)
    ▼
  ┌─────────────────────────────────────────┐
  │  TRUSTED TIER  — handles PHI            │
  │  requires a BAA-covered host            │
  │                                         │
  │  decode → OCR → parse → DE-IDENTIFY     │
  └──────────────────┬──────────────────────┘
                     │  values only: "Glucose 108 mg/dL (ref 70-99) [H]"
                     │  no name, DOB, MRN, address, dates  [verified]
                     ▼
  ┌─────────────────────────────────────────┐
  │  MODEL TIER  — no PHI                   │
  │  commodity GPU is acceptable here       │
  │                                         │
  │  MedGemma → narrative → validation      │
  └─────────────────────────────────────────┘
```

De-identification is an **allowlist**: the text sent onward is reconstructed
from parsed fields, not scrubbed from raw text. A line that could contain a
patient name would never have parsed into a lab value, so it is withheld
rather than filtered. `src/plainmed/deident.py` explains why this is
stronger than a regex scrubber, and `assert_deidentified` re-checks the
output rather than trusting the construction.

**Caveat for counsel:** this implements the mechanical part of HIPAA Safe
Harbor for the text crossing that boundary. Whether the result is
de-identified *as a legal matter* for your data is your determination to
make, not ours. Two things to weigh:

- Lab values in combination are not obviously re-identifying, but we have
  not commissioned an expert determination under 45 CFR 164.514(b)(1).
- If the two tiers run on the same host, the host still handles PHI and
  needs a BAA regardless of the boundary. The boundary only buys you
  something when the tiers are genuinely separated.

## What leaves the device

| Sent | When | To |
|---|---|---|
| Photo or PDF or pasted text | On user action | Trusted tier, over TLS |
| Corrections made on the review screen | On user action | Trusted tier |
| Consent acceptance | Before any processing | Trusted tier |

Nothing else. No analytics, no telemetry, no external fonts, no CDN
requests, no crash reporting. The mobile app loads zero third-party assets
**[verified: no external hosts referenced in `app/mobile/`]**.

## What is stored

Nothing about the report, at any tier. `scripts/retention_check.py` drives a
real request and asserts from outside the application that no file appeared
anywhere and no report content reached any log record.

The audit log persists, by design — HIPAA §164.312(b) requires audit
controls. It records that anonymous session `x` called `/scan/photo` at time
`t` and got `ok` in 1450 ms. It cannot be used to reconstruct a report or
identify a person.

## Client-side storage

None. The mobile client keeps the document in a JavaScript variable. No
localStorage, no sessionStorage, no IndexedDB, no service-worker caching of
report data. Closing the tab ends everything. **[verified: browser storage
is empty after a full session]**

## Known residual risks

State these plainly rather than letting a reader infer more than is true:

1. **Memory is not scrubbed.** Report text exists in process memory during a
   request. A host compromise, core dump, or hypervisor-level attack could
   expose it.
2. **TLS terminates at your load balancer**, which therefore sees plaintext
   PHI and must be in scope for your BAA.
3. **The photo is PHI in transit.** TLS protects it; a compromised client
   device or network interception before TLS does not.
4. **Third-party telemetry would break every claim above.** Error trackers
   and APM agents capture request bodies by default. The PHI log filter
   cannot stop an SDK installed later. This is the single most likely way
   these guarantees silently become false.
