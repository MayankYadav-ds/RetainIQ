# Grouped validation design

Group by exact eight-feature vector. Assign whole groups in descending size. Break ties using a SHA-256 digest of the vector identity and seed 20261127. Minimize the increase in squared class counts relative to each class's per-fold target. Break equal scores by fold index. Require both classes in every fold. The fold policy computes membership before EDA. The immutable local artifact binds membership to dataset and feature-policy versions.

| Validation fold | Non-churn | Churn | Total |
|---|---:|---:|---:|
| 1 | 422 | 75 | 497 |
| 2 | 422 | 75 | 497 |
| 3 | 422 | 74 | 496 |
| 4 | 421 | 74 | 495 |
| 5 | 421 | 74 | 495 |

Every eligible row is in exactly one validation fold. Training uses its complement. Seven projected groups repeat, of which four contain conflicting labels. Their membership stays intact. Grouping addresses exact feature overlap in a snapshot. The source lacks identifiers and calendar cohorts.

For Phase 3, create separate inner grouped splits inside each outer training portion for any tuning, probability calibration or threshold selection. When the same development observations inform feature decisions, report outer results as development-informed estimates. Freeze the complete procedure before one final holdout evaluation. Assess precision-recall, recall/precision at useful thresholds, Brier score and calibration. Consider class weighting and cost-based thresholds inside development. Never rebalance validation or final holdout.
