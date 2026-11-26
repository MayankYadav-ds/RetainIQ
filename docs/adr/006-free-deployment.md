# ADR 006: Free deployment

Date: 2026-11-26
Status: accepted design; implementation scope in architecture overview.

## Context and decision
No billing information or services that may silently charge. Standard public GitHub runners only, no artifact upload/cache action. Hosting remains unprovisioned; recheck terms before every deployment.

## Consequences
Lower Phase 0 operational cost; future features must satisfy the documented release gates.
