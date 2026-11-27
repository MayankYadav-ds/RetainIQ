# Verified UCI acceptance run

2026-11-27, Windows x64, Python 3.11. Official archive directly downloaded from UCI with verified HTTPS. Dataset version `461e2bba687bc6e8f52284c9`, pipeline 1.0. See [source terms and attribution](DATASET_STRATEGY.md).

| Object | Bytes or rows | SHA-256 |
|---|---:|---|
| Original ZIP | 41,943 bytes | `696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66` |
| Customer Churn.csv | 131,728 bytes | `90d5fb6bd1630cd4de4b4d28fcf8b4cb92a8f6ab7484605b0799d47386f7dbe1` |
| Canonical records | 3,150 rows × 15 fields including internal ordinal | `db4bbb548cc23ae66d5d66ab75ab04f49549ac33704f0b665e04b0dd2dd18f53` |

A fresh network-to-publication CLI run took 1.968 seconds. The offline repeat took 0.392 seconds with identical manifests and every artifact hash. Elapsed times include interpreter startup and refer to this host. A separate fresh run recorded a 47,169,536-byte peak working set (about 45.0 MiB) using Windows GetProcessMemoryInfo inside the Python process. This includes interpreter and library memory. The independent Decimal/CSV reconciliation matched every field, ordinal, label and selected feature against the JSONL files. It verified exact partition coverage and duplicate-group disjointness. Development has 2,520 observations, final holdout 630.

The 165 exact duplicate groups include 465 rows (300 copies beyond the first). There are 162 repeated predictor groups, involving 476 rows; 14 groups have conflicting labels, involving 64 rows. No rows were removed. All univariate distribution summaries below are engineering checks. No conditional feature analyses or final-holdout evaluation were performed.

## Aggregate profile

3150 observations, 13 predictors, one target. Missing cells: 0.
Target counts {'0': 2655, '1': 495}. Prevalence 15.7143%.
Exact duplicate excess 300. Repeated predictor groups 162; conflicting groups 14.

| Field | Missing (%) | Distinct | Min | Q1 | Median | Q3 | Max | Mean | Sample SD | Frequencies |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| call_failure | 0 | 37 | 0 | 1 | 6 | 12 | 36 | 7.6279 | 7.2639 |  |
| complains | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0.076508 | 0.26585 | {'0': 2909, '1': 241} |
| subscription_length | 0 | 45 | 3 | 30 | 35 | 38 | 47 | 32.542 | 8.5735 |  |
| charge_amount | 0 | 11 | 0 | 0 | 0 | 1 | 10 | 0.94286 | 1.5211 | {'0': 1768, '1': 617, '2': 395, '3': 199, '4': 76, '5': 30, '6': 11, '7': 14, '8': 19, '9': 14, '10': 7} |
| seconds_of_use | 0 | 1756 | 0 | 1391.2 | 2990 | 6478.2 | 17090 | 4472.5 | 4197.9 |  |
| frequency_of_use | 0 | 242 | 0 | 27 | 54 | 95 | 255 | 69.461 | 57.413 |  |
| frequency_of_sms | 0 | 405 | 0 | 6 | 21 | 87 | 522 | 73.175 | 112.24 |  |
| distinct_called_numbers | 0 | 92 | 0 | 10 | 21 | 34 | 97 | 23.51 | 17.217 |  |
| age_group | 0 | 5 | 1 | 2 | 3 | 3 | 5 | 2.826 | 0.89256 | {'1': 123, '2': 1037, '3': 1425, '4': 395, '5': 170} |
| tariff_plan | 0 | 2 | 1 | 1 | 1 | 1 | 2 | 1.0778 | 0.26786 | {'1': 2905, '2': 245} |
| status | 0 | 2 | 1 | 1 | 1 | 1 | 2 | 1.2483 | 0.43207 | {'1': 2368, '2': 782} |
| age | 0 | 5 | 15 | 25 | 30 | 30 | 55 | 30.998 | 8.8311 |  |
| customer_value | 0 | 2654 | 0 | 113.8 | 228.48 | 788.39 | 2165.3 | 470.97 | 517.02 |  |
| churn | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0.15714 | 0.36399 | {'0': 2655, '1': 495} |

## Warnings

- extreme, subscription_length: 18 rows. Outside outer Tukey fences. Retain and review.
- extreme, charge_amount: 95 rows. Outside outer Tukey fences. Retain and review.
- extreme, frequency_of_sms: 186 rows. Outside outer Tukey fences. Retain and review.
- extreme, age: 170 rows. Outside outer Tukey fences. Retain and review.
- documented_range, charge_amount: 7 rows. Observed band 10 exceeds documented 9. Preserve; withhold from default features.
- exact_duplicates, all: 465 rows. Matching canonical vectors. Retain all observations and group partitions.
- predictor_duplicates, all: 476 rows. Matching canonical vectors. Retain all observations and group partitions.
- conflicting_labels, all: 64 rows. Matching canonical vectors. Retain all observations and group partitions.
