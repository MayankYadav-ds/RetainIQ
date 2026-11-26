# ADR 007: Guest isolation

Date: 2026-11-26
Status: accepted design; implementation scope in architecture overview.

## Context and decision
Defer guest workflows until server-derived workspace scope, expiry cleanup, quotas and cross-tenant tests exist. Phase 0 exposes public metadata only; no guest isolation is implemented.

## Consequences
Lower Phase 0 operational cost; future features must satisfy the documented release gates.
