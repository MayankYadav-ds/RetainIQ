# RetainIQ handoff · 2026-11-28

**Phase 2 COMPLETE. Version 0.3.0.** Phase 2 adds a verified development-only statistical workspace and feature engineering pipeline. Phase 1 source registry, Data Explorer and API readiness remain operational. Service expenditure is INR 0. The application runs locally. No public deployment, model training or estimator benchmarking occurred.

## Scientific scope

Source dataset 461e2bba687bc6e8f52284c9 was verified against its pinned raw and normalized checksums. The eight approved operational fields created 16 shared projected groups across the original 2,520/630 split. The pre-analysis rule quarantined 40 development observations, leaving 2,480. Seventy-eight held-out observations were in the shared groups. The holdout checksum before and after analysis was e9509c84629e8e03827d8d27823216c9a890b86cc589f7afa77b1265584ba63a. No holdout label was selected by the auditor or used by any analytical operation. See [partition integrity](PARTITION_INTEGRITY.md).

Five grouped validation folds retain both classes and preserve duplicate groups. The report documents the 15.0% eligible churn prevalence, feature associations, distribution tails and empirical redundancy. The feature catalog provides three unfitted candidates and a shared batch/single-record transform. The demonstration preprocessing state applies only to the identified development training fold. See [EDA](EXPLORATORY_DATA_ANALYSIS.md), [statistics](STATISTICAL_ANALYSIS.md), [folds](VALIDATION_FOLDS.md) and [feature catalog](FEATURE_CATALOG.md).

## Reproduction and validation

See [commands and API opt-in](FEATURE_ENGINEERING.md). Real UCI run view 136a09a0f2ec6a66bf3ca6f3 reproduced identical hashes in 0.856 and 0.875 seconds including interpreter startup. A separate Windows Python process recorded peak working set 52,260,864 bytes (49.84 MiB). Both preprocessing families had zero non-finite values and all three variants matched batch and individual results. Independent reconciliation used arithmetic distinct from the main implementation.

| Local artifact | SHA-256 |
|---|---|
| Aggregate JSON | 4b80d2dbf5dfd1f680c2bd055c01cc1aa54527780d589b1ebc8099feb647a426 |
| Aggregate Markdown | 7c846809c8dbc1de1875b159c3f725512530db7ae89c856d44459d4905c68664 |
| Fold membership | 82a46397d506eca6252994b2999fb2013a01579aa5c49ab49fa53abcd38bd776 |
| Feature matrices | ab3cf764019b67d1e3085ee70ddd5a07e7474e98899c80f37c1721428d7706c7 |
| Fold demonstration state | e1f18e108d266733f7db4075345bf97598c1179e4ee58ea79118ef4ef9af01a2 |

Windows passed Ruff lint and formatting, strict Mypy, ESLint, TypeScript, Vite build, pip check and whitespace review. Pytest 55/55, Vitest 11/11, Chromium 4/4. Screenshots of the three real aggregate pages were captured locally. Existing TestClient and intentional duplicate ZIP warnings remain. A frontend optional-binding startup failure was resolved with npm ci --include=optional; the lock versions did not change.

Implementation commit 7a55c17670b0cd784093116f76bafd7237e8da62 passed 55 backend, 11 frontend and 4 browser tests, plus lint, formatting, strict typing, build, dependency and whitespace checks, in the [hosted release workflow](https://github.com/MayankYadav-ds/RetainIQ/actions/runs/46117999712). The handoff commit changes documentation only. Hosted CI uses deterministic synthetic records. Real-data verification across Linux and Windows was not performed.

## Next authorized phase

Phase 3 can use the frozen eligible view and outer fold assignments for model development. Establish inner grouped folds for tuning, calibration and threshold choice and freeze these choices before using the final holdout. Leave status, customer value, charge band and demographic fields outside operational predictors. Source IDs, event timestamps, treatment effects and exact horizons remain unavailable. Customer independence cannot be proven. Demographic subgroup exploration, deployment, PostgreSQL, Docker and tenant authentication were outside this phase.

Starting commit e61a258d1fd71b4c0d5c9f9c070304fe5cfdcf25. The [Phase 1 handoff](https://github.com/MayankYadav-ds/RetainIQ/blob/e61a258d1fd71b4c0d5c9f9c070304fe5cfdcf25/docs/PROJECT_STATE.md) preserves acquisition evidence. Phase 2 commits are listed in the local main branch history.
