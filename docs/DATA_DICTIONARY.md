# Iranian Churn · schema v1

The official ZIP contains one file, Customer Churn.csv. All fields are required and non-null. Integers must parse as integers. Customer Value is a finite nonnegative number. The canonicalizer trims and collapses whitespace and normalizes case, rejects collisions, unexpected/missing fields, negative values and invalid category codes. Exact source spellings appear in code spans below. Observed extrema are descriptive rather than clipping rules. Counts have no verified upper business limit. Source descriptions and codes come from the [UCI catalog](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset).

| CSV header | Canonical field | Meaning and unit | Domain or observed bounds | Default use |
|---|---|---|---|---|
| `Call  Failure` | call_failure | Failed calls, count | Nonnegative; observed 0–36 | Approved |
| `Complains` | complains | Complaint indicator | 0 no, 1 yes | Approved |
| `Subscription  Length` | subscription_length | Tenure in months | Nonnegative; observed 3–47 | Approved |
| `Charge  Amount` | charge_amount | Ordinal charge band, no currency | Documented 0–9; observed 0–10. Preserve 10 with warning | Conditional, off |
| `Seconds of Use` | seconds_of_use | Call usage, seconds | Nonnegative; observed 0–17,090 | Approved |
| `Frequency of use` | frequency_of_use | Calls, count | Nonnegative; observed 0–255 | Approved |
| `Frequency of SMS` | frequency_of_sms | Text messages, count | Nonnegative; observed 0–522 | Approved |
| `Distinct Called Numbers` | distinct_called_numbers | Distinct destinations called, count | Nonnegative; observed 0–97 | Approved |
| `Age Group` | age_group | Ordered demographic category | 1 younger through 5 older | Audit only |
| `Tariff Plan` | tariff_plan | Nominal subscription plan | 1 pay-as-you-go, 2 contractual | Approved |
| `Status` | status | Account activity state | 1 active, 2 non-active | Excluded |
| `Age` | age | Age-like demographic value; exact vs representative age unverified | Nonnegative; five distinct values, 15–55 | Audit only |
| `Customer Value` | customer_value | Calculated customer score; unit unspecified | Numeric; observed 0–2165.28 | Requires evidence |
| `Churn` | churn | State at end of month twelve | 0 non-churn, 1 churn | Target only |

Timing evidence is dataset-level: the publisher assigns predictors to months 1–9 and the outcome to month 12. No column has individual availability timestamps. The archive includes Age and Age Group, with five distinct values in each; their pairing is redundant in this file (see eligibility audit). UCI mentions an anonymous customer ID in prose, but none appears in the archive. The CSV has 13 predictors plus one target. Its customer value includes decimals despite the catalog's broad integer type description. The output adds a source-row ordinal for reconciliation only.

Type, missingness, invalid category, unsupported columns and impossible negative values block publication. Band 10, duplicates, conflicts, extreme and concentrated distributions produce warnings with evidence and handling. A new unreviewed band beyond 10 is rejected. No row exclusion, deduplication, clipping or imputation occurred. Compare [aggregate evidence](DATA_QUALITY_REPORT.md) and [eligibility](FEATURE_ELIGIBILITY.md).
