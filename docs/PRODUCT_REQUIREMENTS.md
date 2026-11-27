# Product requirements — v0.1.0
## Problem and organizations
Subscription businesses need defensible prioritization of retention work under limited budgets.
Target organizations are small telecom, SaaS and subscription analytics teams with lawful customer data.
## Personas and workflows
- Data scientist: register licensed data; audit timestamps; compare baselines; calibrate; publish a versioned evaluation.
- Retention manager: select workspace and budget; inspect risk and explanations; compare assumption-based interventions; export a reviewed plan.
- Business analyst: inspect segments, missingness and contribution margin at risk; disclose uncertainty.
- Recruiter: enter without registration into a disposable isolated sample workspace; inspect provenance,
  evaluation, explanations and working simulations. This workflow is future scope.
## North-star metric
Incremental retention contribution margin = observed treatment contribution margin minus estimated
counterfactual contribution margin minus incremental intervention costs over a prespecified window.
For a randomized campaign, compare mean contribution margin per eligible assigned customer across
treatment and holdout (intention to treat), multiply the difference by the treated cohort size,
and subtract incremental campaign cost once. Fix the measurement window, currency and margin
definition before enrollment. Report uncertainty and attrition. Predicted churn reduction,
modeled savings and scenario ROI are not observed impact. No impact claims exist in Phase 0.
## Functional requirements
Phase 0: live/readiness/version APIs, typed settings, database probe, accessible responsive shell,
theme controls, loading/error/empty states and actual API verification. No prediction endpoints.
MVP: lawful ingestion and manifests, leakage audit, meaningful baselines, calibrated risk, subgroup
reports, SHAP, risk segments and assumption-labeled retention scenarios.
Final: data-justified 30/60/90-day horizons, margin risk, budget optimization, strategy simulation,
drift and performance monitoring, authentication, isolated guest workspaces and public recruiter demo.
## Non-functional requirements
Local Windows x64 operation within 16 GB RAM; sequential resource-intensive work; no GPU requirement.
No paid dependencies or billing; deterministic acquisition/experiment records; validated schemas;
keyboard operation and WCAG 2.2 AA intent, with manual audit required before claiming conformance.
No secrets or personal records in Git; no private data in unauthenticated routes or logs.
## Scope and non-goals
Phase 0 is application infrastructure. No model, ingestion, causal effect estimate, authentication,
workspace persistence or full SaaS dashboard is delivered. No arbitrary accuracy guarantee.
MVP excludes real-time streaming, Kubernetes and automatic customer contact.
## Acceptance and success
All Phase 0 gates in PROJECT_STATE must be reproducible. Measure endpoint semantics, negative paths,
frontend connectivity and clean build; do not fabricate latency targets or business results.
Later success: calibration/Brier/PR-AUC and ranking lift against baselines, reproducible evaluations,
workflow completion and experimentally measured incremental contribution margin with intervals.
## Privacy, deployment and limitations
Use lawful minimized data; document purpose, retention, deletion and license before ingestion.
Demo permits only explicitly synthetic or redistribution-approved samples. Public guest access must
wait for tested isolation. Free hosted storage may be ephemeral; local execution is authoritative.
Snapshot benchmarks do not establish longitudinal generalization or intervention effectiveness.
