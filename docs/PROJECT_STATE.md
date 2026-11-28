# RetainIQ handoff · 2026-11-28

**Phase 3 COMPLETE. Version 0.4.0.** Phase 3 adds nested grouped benchmarking, an evaluated and reloadable calibrated champion, Model Lab and the prediction simulator. Service expenditure INR 0. Local execution only. No production deployment or explanation integration.

## Frozen evidence

Original UCI version 461e2bba687bc6e8f52284c9, eligible view 136a09a0f2ec6a66bf3ca6f3. All frozen references verified before training. The five outer folds remain as published in Phase 2. The benchmark attempted 210 configurations over five outer folds for seven learned models. All completed. Two reference baselines completed. The second development benchmark reproduced OOF prediction bytes. Read the [protocol](ML_EXPERIMENT_PROTOCOL.md) and [benchmark results](MODEL_BENCHMARK.md).

Frozen model 2234d0279bb9bd18d77c27b3 is histogram gradient boosting with FS01, balanced class weights, 100 iterations and 15 maximum leaf nodes. Sigmoid calibration won on the disjoint policy set. Operating threshold 0.28. Artifact 589,194 bytes. Local restoration reproduced original probabilities exactly. [Calibration](PROBABILITY_CALIBRATION.md) · [Registry and trust boundary](MODEL_REGISTRY.md)

The final receipt 6f0e95d28d791f4d703cdac4743432f762805a0374f24569bbb878f33f034b79 records one evaluation of all 630 held-out rows and the prespecified reference baselines. AP 0.8061, ROC-AUC 0.9598 and Brier 0.05752. No scientific choices changed after holdout access. Independent arithmetic checked metrics, ranking, calibration and frozen threshold. A repeat command verified and returned the same receipt without recomputing predictions. Private OOF rows, final predictions, memberships and model artifacts remain ignored. [Final evaluation](FINAL_EVALUATION.md)

## Verification

Windows passed 58 Pytest, 13 Vitest and 5 Playwright tests. Local checks included Ruff lint and format, strict Mypy, ESLint, TypeScript, Vite build, pip check and Git whitespace review. The fitted UCI model was exercised through real Model Lab and Prediction simulator pages, existing analytical views, a 100-record batch and strict input rejection. Browser screenshots contain aggregate evidence and invented inputs. Servers were stopped afterward.

The executable release is commit 9f9d7e39dec1cb8f92e8850955a38224e3b00a9d. [Hosted Ubuntu workflow](https://github.com/MayankYadav-ds/RetainIQ/actions/runs/46155686489). Hosted Ubuntu passed 58 Pytest, 13 Vitest and 5 Chromium tests plus all applicable quality gates. It ran a bounded synthetic nested benchmark and actual browser inference with a synthetic-trained verified model. The current workflow actions emit a Node runtime deprecation notice. The handoff commit changes documentation only.

TestClient deprecation and deliberately duplicated ZIP-member warnings predate the phase. The initial synthetic training test exposed insufficient minority support for five inner role folds. Synthetic-only quick mode now uses four role folds and two core folds. The real benchmark and final protocol stayed fixed. No Docker, PostgreSQL, genuine Ubuntu benchmark or external validation was run. Local skops and optional boosters require trusted artifacts, exact dependencies and OS access controls.

## Phase 4 handoff

Use the stored ordered FS01 design and underlying estimator decision margin for tree explanation research. Verify SHAP support for the exact estimator and additivity on the raw margin. Calibration is a separate nonlinear probability transform. Do not attempt to apply it to individual feature contributions. Future model changes require fresh independent data. The UCI holdout is consumed by this procedure. No Phase 4 work was started. [Model card](MODEL_CARD.md) · [Operator commands](PREDICTION_API.md)

Starting commit 7200243d5c91af1cb1fb485f49b4d3eb1c2cab82. [Phase 2 handoff](https://github.com/MayankYadav-ds/RetainIQ/blob/7200243d5c91af1cb1fb485f49b4d3eb1c2cab82/docs/PROJECT_STATE.md).
