# Subprocessors and vendor agreements

> **Tracker — complete as you select vendors.** A vendor that can touch PHI
> without a signed agreement in place makes the processing unlawful, not
> merely risky. Do not launch with an unchecked box in the "Signed" column.

**Last updated: [DATE]**

## Required agreements

| Vendor | Role | Sees PHI? | Agreement needed | Signed? | Date |
|---|---|---|---|---|---|
| [CLOUD HOST] | Trusted tier compute | **Yes** | BAA (US) / DPA + SCCs (EU/UK) | ☐ | |
| [GPU PROVIDER] | Model tier inference | No — de-identified only | DPA | ☐ | |
| [CDN / WAF] | TLS termination, edge | **Yes — sees plaintext** | BAA / DPA | ☐ | |
| [LOG / SIEM] | Audit records | No | DPA | ☐ | |
| [EMAIL PROVIDER] | Support correspondence | Possibly | BAA / DPA | ☐ | |
| [MONITORING] | Uptime, metrics | No, if body capture is off | DPA | ☐ | |

## Notes that matter

**TLS terminators see everything.** A CDN or load balancer that terminates
TLS handles plaintext PHI and is in scope for a BAA, even though it only
passes traffic through. This is routinely missed.

**Support email is a PHI channel.** Users will paste report contents into
support requests regardless of what you tell them. Either treat the email
provider as a business associate, or use a support tool that is covered.

**Cheap GPU providers generally will not sign a BAA.** Community and spot
tiers on commodity GPU marketplaces are explicitly out of scope for
compliance programmes. This is survivable here *only* because the model tier
receives de-identified data — see [data-flow.md](data-flow.md). If that
boundary is ever weakened, the GPU provider immediately needs a BAA and the
cheap tiers stop being available to you.

**A model licence is not a data agreement.** Google's Health AI Developer
Foundations terms govern your use of the MedGemma weights. They are not a
BAA and say nothing about your patients' data.

## Publication

GDPR expects data subjects to be able to see who processes their data.
Publish the completed list at [SUBPROCESSORS URL] and link it from the
privacy notice. Give notice before adding a subprocessor.
