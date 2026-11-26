# ML integrity contract
Binding on all future experiments; no ML has been implemented in Phase 0.
1. Define churn, population, prediction timestamp, observation window and outcome window before modeling.
2. Features must be point-in-time correct. Audit availability times, future information and target leakage.
3. Prevent customer-level contamination when repeated observations or grouped entities exist.
4. Separate training, validation and untouched final testing; prefer temporal splits for longitudinal data.
   Snapshot data must disclose inability to validate temporal generalization.
5. Fit preprocessing, imputation, resampling and feature selection on training partitions only.
6. Treat censoring explicitly; do not label insufficient follow-up as non-churn.
7. Evaluate imbalance and meaningful dummy, prevalence and simple linear baselines.
8. Calibrate probabilities on an appropriate training/validation partition; select thresholds on validation only.
9. Freeze the final test set; record seeds, dataset checksums, schema, dependencies and split membership.
10. Report uncertainty, subgroup sample sizes, limitations and failed experiments. No accuracy guarantees.

Required evaluation as applicable: ROC-AUC, PR-AUC (specify integration convention), precision,
recall, F1, Brier score, calibration curves, precision/lift/recall at K, revenue-weighted recall,
and relevant customer subgroup performance. Define K and revenue weighting before final evaluation.
Report confidence intervals using resampling appropriate to temporal and customer dependence.

SHAP describes a model's predictive associations relative to a stated background; it establishes
neither causality nor intervention effectiveness. Without randomized treatment data or a defensible
causal identification strategy, effects and ROI are assumption-based scenario estimates, labeled
in UI, exports and reports. Sensitivity analysis must vary these assumptions.
Horizons require timestamps and sufficient follow-up; do not invent 30/60/90-day targets.
Model release requires provenance, leakage review, calibration, evaluation and artifact checksum approval.
