# Permanent engineering constraints
Stop after Phase 3 until Phase 4 is authorized. Treat the original holdout as consumed by the frozen Phase 3 procedure and never use it to tune later models. Use the frozen audited eligible view for exploratory analysis and grouped training. Fit preprocessing only inside each development training fold. Never expose protected holdout rows, membership, raw records or private paths. Bump pipeline identity on output-affecting changes. Read docs/PROJECT_STATE.md first.
Keep total expenditure at INR 0: no billing details, paid services or paid runners.
Preserve unrelated repositories and existing remotes; never force-push.
Never commit secrets, customer data, restricted datasets, caches or model artifacts.
Use a local-first modular monolith; Windows, Python 3.11 and Node 24 must remain supported.
Run applicable quality gates before committing. Record actual results and blockers.
Never invent data, outcomes, evaluation scores, deployment URLs or successful checks.
Follow docs/ML_INTEGRITY_CONTRACT.md. SHAP is not causal evidence.
Guest isolation and authentication are planned, not implemented. Do not expose private data.
No heavy ML dependencies until required. Update project state when behavior changes.
