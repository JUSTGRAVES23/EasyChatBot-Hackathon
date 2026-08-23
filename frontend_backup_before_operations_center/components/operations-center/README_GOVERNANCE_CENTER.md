# Governance Center consolidation

The Governance Center now uses the existing governance backend as a
read-only projection.

Canonical route:

`/operations-center/governance`

Canonical data endpoints:

- `/operations/governance/status`
- `/operations/governance/timeline`

YETI is a governance explanation layer only. It has no control authority.

The email integration remains separate and continues through the existing
Email Service / Provider Manager / Resend infrastructure.

This consolidation intentionally avoids creating a second governance
backend or a separate YETI screen.
