# ADR 005: Explainability and causal inference

Date: 2026-11-26
Status: accepted design; implementation scope in architecture overview.

## Context and decision
SHAP explains model associations only. Treatment ROI requires randomized evidence or an explicit identification strategy. Otherwise scenario effects remain assumptions.

## Consequences
Lower Phase 0 operational cost; future features must satisfy the documented release gates.
