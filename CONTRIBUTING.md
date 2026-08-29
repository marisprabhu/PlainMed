# Contributing to PlainMed

Thanks for looking. PlainMed explains people's medical reports back to them,
so a few of its rules are stricter than a typical project's. Everything here
exists because of that, not out of ceremony.

## Getting set up

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate elsewhere
pip install -e ".[dev]"
python -m pytest
```

Then the three proofs, which must also pass:

```bash
python scripts/offline_check.py
python scripts/retention_check.py
python scripts/deident_check.py
```

`python scripts/demo.py` walks through what the system does in about seven
seconds, which is the fastest way to understand it.

## Four rules that are not negotiable

These are the properties the project exists to guarantee. A change that
weakens one is not a trade-off to discuss in review; it is a different
product.

**1. Numbers never come from a language model.** Values, units, ranges and
flags are extracted by `extract/lab_parser.py` and nothing else. A generated
`13.5` cannot be told apart from a hallucinated one, so the model is never
given the opportunity. If a feature needs the model to produce a number,
the feature needs redesigning.

**2. Nothing is explained before a human confirms what was read.** The
review step is mandatory, not conditional on low confidence. Confidence
tells you the OCR was *sure*, not that it was *right* — we have a real case
where a unit was misread with high confidence.

**3. No identifier reaches the model tier.** `deident.py` rebuilds text from
parsed fields rather than scrubbing it. If you add a field that crosses that
boundary, add it to `deident_check.py` too.

**4. Nothing is written to disk or logs.** No caching of report content, no
temp files, no debug logging of anything a patient supplied.

## Changes that are regulatory, not just technical

`src/plainmed/safety.py` and `src/plainmed/pipeline/validate.py` are why
PlainMed is not a regulated medical device: it describes a document and
refuses to diagnose. Loosening the forbidden-claim checks — adding "your
result suggests…", a risk score, a triage prompt — could reclassify the
software under CDSCO (India), FDA (US) or MDR (EU).

Please do not weaken these without opening an issue first. It is a
conversation about regulatory exposure, not code style.

The same applies to `glossary/data/glossary.json`. It is the only place
PlainMed asserts medical meaning in its own voice. Definitions must be
descriptive ("this test measures…") and must never imply what a result means
for a person. A test enforces the absence of diagnostic language, but it
cannot judge whether a definition is *correct* — see Clinical review below.

## Adding a language

Notice translations live in `src/plainmed/compliance/translations.py`. Adding
one is a data change: add an entry to `ITEMS`, `TEXT` and `ENDONYMS`, then
register it in `_BUILDERS` in `notice.py` and add the option to the picker in
`app/mobile/index.html`.

**Translations must be reviewed by a qualified translator before shipping.**
A consent notice is the document a patient relies on to understand what
happens to their data; a mistranslation is an invalid consent, not a
cosmetic bug. The translations currently in the repo have not had that
review, and the module says so.

## Clinical review

The glossary has not been reviewed by a clinician. If you have the
qualifications to do that, it is the single most valuable contribution
available — more than any code change. Open an issue and say so.

## Code style

Match the surrounding code. Beyond that:

- Comments explain **why**, not what. The repo has a lot of "this is
  deliberate, here is the trade" — keep that.
- Every claim in a docstring should be true. If something is not yet
  measured or verified, say so plainly rather than implying otherwise.
- New behaviour needs a test. Safety-relevant behaviour needs a test that
  fails loudly when the property is broken, not one that quietly passes.

## Pull requests

Say what changed and why. If it touches one of the four rules or the
regulatory files, say that explicitly in the description so a reviewer does
not have to notice it.

CI runs the tests on Python 3.10–3.13, the three proofs, and a check that
refuses telemetry dependencies. All must pass.

## What this project is not

Not a medical device. Not clinically validated. Not reviewed by a clinician.
Do not deploy it to real patients without reading
[legal/README.md](legal/README.md) — there is a substantial gap between
"working software" and "lawful service", and that document lists it.
