# RetainIQ handoff · 2026-11-27

**Phase 1 COMPLETE. Version 0.2.0.** Project spend INR 0. Local Windows x64 and hosted Ubuntu pass. The public repository is [MayankYadav-ds/RetainIQ](https://github.com/MayankYadav-ds/RetainIQ). The application runs locally; there is no public application deployment. Phase 2 requires separate authorization.

## What is available

Run the [operator workflow](DATA_ENGINEERING.md) to acquire the official UCI archive or import its pinned bytes offline, validate, profile, normalize and publish a version. Immutable raw objects and staged, verified JSONL versions live outside Git. The local registry and read-only aggregate API power the Data Explorer. The Phase 0 readiness and liveness semantics are preserved. Source registration and approval require code/configuration review. There are two functional sources: the pinned UCI snapshot and an explicitly synthetic test fixture.

Real-data acceptance independently reconciled every row against the archived CSV, confirmed grouped partition integrity and reproduced identical artifacts on repeated execution. See the [quality report](DATA_QUALITY_REPORT.md), [dictionary](DATA_DICTIONARY.md), [eligibility audit](FEATURE_ELIGIBILITY.md) and [target/split contract](EVALUATION_PROTOCOL.md). The UCI version is `461e2bba687bc6e8f52284c9`. It contains 2,520 development rows and 630 protected final rows. The source supports snapshot classification only. No ML model or intervention effect was estimated.

## Verification

Implementation commit `bc539525de398b267270acd2a0ca49fb0e9f3df7` passed [hosted CI](https://github.com/MayankYadav-ds/RetainIQ/actions/runs/45946032028). The handoff changes documentation only. Both platforms used Python 3.11, Node 24 and Chromium for browser tests.

| Command | Windows total / passed / failed / skipped | Hosted Ubuntu total / passed / failed / skipped |
|---|---|---|
| python -m pytest backend/tests -q | 51 / 51 / 0 / 0 | 51 / 51 / 0 / 0 |
| npm test | 10 / 10 / 0 / 0 | 10 / 10 / 0 / 0 |
| npm run e2e | 3 / 3 / 0 / 0 | 3 / 3 / 0 / 0 |

Non-counted gates passed on both platforms: Ruff lint, Ruff format, strict Mypy, ESLint, TypeScript, production Vite build, pip check and Git whitespace checks. Windows also passed an independent clean-venv install/verify, fresh real acquisition, offline idempotency, independent CSV reconciliation and a browser check of the real benchmark at the native dev URL. API docs and readiness returned 200. Test servers were stopped. Hosted CI used deterministic synthetic records. No hosted real-data run or cross-OS real-data hash comparison was performed.

## Limitations and recovery

The TestClient emitted its existing httpx deprecation warning. The negative archive test intentionally produces Python's duplicate-member warning. Windows uses the documented pure-Python SQLAlchemy build. Docker and PostgreSQL were outside Phase 1 validation. The pipeline is intentionally bounded for compact snapshots (2 MB input, 10,000 rows); profiling and group audits are in memory. Local administrators can read both partitions. No authenticated tenant isolation, hostile multiuser filesystem, crash-durable transaction guarantee or public deployment has been validated. Read the [privacy boundary](DATA_PRIVACY.md) before changing publication policy. The source registry pins exact bytes; future upstream revisions require explicit review. KKBox access and IBM file-level redistribution rights remain unresolved.

## Next phase

Use only the development reader and the eight approved predictors for initial exploration. Preserve source version, grouping and held-out membership; design internal grouped folds and freeze preprocessing and model selection before final evaluation. Resolve charge-band semantics, status timing and the value-score formula before expanding eligibility. They do not block work on approved development fields. Age and age group remain available for controlled auditing. No Phase 2 analysis has started.

## History

Starting main commit `ab9e56facd58925055700f635c48c71ee1caace5`. Phase 1 implementation: ec2bdb6 (source/security contracts), ea12f2e (quality and grouping), 1687b31 (registry/CLI), 53e038a (aggregate API and temporal contracts), fac0ca3 (Data Explorer), bc53952 (regression tests and independent reconciliation). Use git log -1 for the final handoff commit. The original [Phase 0 handoff](https://github.com/MayankYadav-ds/RetainIQ/blob/ab9e56facd58925055700f635c48c71ee1caace5/docs/PROJECT_STATE.md) records its six commits and validation.
