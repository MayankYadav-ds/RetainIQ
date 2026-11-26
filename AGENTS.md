# Permanent engineering constraints
Phase 0 only until the user authorizes Phase 1. Read docs/PROJECT_STATE.md first.
Keep total expenditure at INR 0: no billing details, paid services or paid runners.
Preserve unrelated repositories and existing remotes; never force-push.
Never commit secrets, customer data, restricted datasets, caches or model artifacts.
Use a local-first modular monolith; Windows, Python 3.11 and Node 24 must remain supported.
Run applicable quality gates before committing. Record actual results and blockers.
Never invent data, outcomes, evaluation scores, deployment URLs or successful checks.
Follow docs/ML_INTEGRITY_CONTRACT.md. SHAP is not causal evidence.
Guest isolation and authentication are planned, not implemented. Do not expose private data.
No heavy ML dependencies until required. Update project state when behavior changes.
