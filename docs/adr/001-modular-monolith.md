# ADR 001: Modular monolith

Date: 2026-11-26
Status: accepted design; implementation scope in architecture overview.

## Context and decision
Keep one deployable API with explicit API, configuration and infrastructure boundaries. Service extraction requires measured operational need. Avoid queues and network failure surfaces in Phase 0.

## Consequences
Lower Phase 0 operational cost; future features must satisfy the documented release gates.
