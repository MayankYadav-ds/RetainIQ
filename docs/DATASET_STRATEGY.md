# Dataset acquisition strategy
Research date: 2026-11-26. No data downloaded; access and terms must be rechecked at acquisition.

## UCI Iranian Churn — development benchmark
[Official source](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset).
3,150 customers, 13 features; CSV about 129 KB (41 KB download). CC BY 4.0 permits reuse with
attribution. Public access, no Kaggle credentials. Nine-month aggregates precede month-12 labels
by a three-month planning gap. Fields cover usage, complaints, subscription length, tariff,
age, status and calculated customer value; label is binary churn. No intervention assignments.
No individual event history: cannot derive arbitrary daily horizons or perform a genuine calendar
holdout from absent dates. Audit Status/Customer Value definitions for leakage. Preserve attribution
and change notices on redistribution; retain exact schema/checksum only after legitimate acquisition.

## KKBox — advanced candidate, gated
[Data](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/data),
[rules](https://www.kaggle.com/competitions/kkbox-churn-prediction-challenge/rules).
Competition account and accepted terms are required; access not tested. Renewal beyond a
30-day expiration gap defines churn. Member, transaction and dated listening-log tables support
temporal design, subject to label and event-availability audits. No randomized intervention effects.
Full logs are multi-GB and exceed comfortable in-memory use here; exact current archive sizes were
not exposed in the retrieved official page and remain unverified. Do not use third-party size claims
as acquired-file metadata. Inspect official inventory after authorized access and plan DuckDB batches.
Rules restrict access and redistribution to eligible participants and permitted purposes. Public demo
redistribution is NOT approved. Do not commit data, share records or bypass terms. If lawful use is
uncertain, select UCI instead; this candidate is not a prerequisite for local app use.

## IBM Telco — supplementary sample
[Official archived repository](https://github.com/IBM/telco-customer-churn-on-icp4d),
[data directory](https://github.com/IBM/telco-customer-churn-on-icp4d/tree/master/data).
Repository uses Apache-2.0; verify any dataset-specific notice before redistribution. Public source,
no account needed to read. Common CSV is about 1 MB, 7,043 snapshot customers; verify exact dimensions
and bytes at acquisition. Demographic/service/account fields, tenure and charges accompany a binary
Churn label. No event-level observation timeline or intervention assignment. Snapshot labels cannot
justify 30/60/90-day prospective claims or intervention ROI. IBM describes sample data; do not portray
it as production customer evidence. Preserve license/NOTICE requirements if applicable.

## Phase 1 acquisition gates
Approve intended purpose/license, record access terms and source; checksum original files; validate
manifest against data/manifest.schema.json with format checking; profile schema/duplicates/missingness;
record target semantics and unsupported horizons; audit leakage and lawful retention. Use no PII in
Git. Unsupported horizons use an empty list, never invented labels. Synthetic demo fixtures require
explicit labeling and reproducible seeds. No ingestion or training belongs to Phase 0.
