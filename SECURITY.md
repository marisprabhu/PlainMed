# Security policy

PlainMed processes medical reports. A defect here can expose someone's
health information, so security reports are welcome and taken seriously.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private reporting: **Security → Report a vulnerability** on this
repository. If that is unavailable, email `[SECURITY CONTACT EMAIL]`.

Please include what you found, how to reproduce it, and what an attacker
could achieve. A proof of concept helps but is not required.

We aim to acknowledge within 3 working days and to give an assessment within
14 days. If you would like credit in the fix, say so.

## Please do not

- Test against anyone else's deployment of PlainMed.
- Use real patient data in your testing. The `samples/` directory contains
  synthetic reports for exactly this purpose.
- Access, alter or retain data that is not yours.

## What we consider a vulnerability

The properties below are the ones the project claims. Anything that breaks
one is in scope, and the first three are the most serious:

| Property | Enforced by |
|---|---|
| Report content is never written to disk or to any log | `api/retention.py`, `scripts/retention_check.py` |
| No identifier reaches the model tier | `deident.py`, `scripts/deident_check.py` |
| Explanations cannot contain unsupported claims | `pipeline/validate.py`, `safety.py` |
| Nothing is processed without consent | `api/security.py` |
| Under-18s are excluded | `api/security.py` |

Also in scope: authentication bypass, rate-limit bypass, prompt injection
that changes application behaviour, dependency vulnerabilities with a
practical path to exploitation, and anything that makes the model tier
receive identifiable data.

## Known limitations, not vulnerabilities

These are documented trade-offs. Reports about them are still welcome as
discussion, but they are not treated as vulnerabilities:

- **Memory is not scrubbed.** Report text exists in process memory during a
  request. A host compromise or core dump could expose it.
- **TLS terminates upstream.** Whatever terminates TLS sees plaintext.
- **No authentication of identity.** Sessions are deliberately anonymous;
  the system cannot tell users apart, by design.
- **The self-signed certificate** from `scripts/make_dev_cert.py` is for
  local testing only and is not trusted by anything.
- **Model output quality.** MedGemma is not clinically validated. This is
  why the validator exists; a poor explanation that passes validation is a
  product limitation, not a security issue.

## For anyone deploying this

The application enforces what it can. Everything else is yours:

- TLS 1.2+ with HSTS, and never expose the app port directly.
- Set `PLAINMED_SECRET_KEY`; the app refuses to start in production without it.
- Keep the model tier on a private network.
- **Install no telemetry or APM agent that captures request bodies.** This is
  the most likely way the guarantees above silently stop being true — CI
  fails the build if such a dependency appears, but that cannot protect a
  deployment you configure yourself.
- Read [legal/README.md](legal/README.md) before processing real reports.
