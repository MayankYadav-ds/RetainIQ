# Feature catalog

All features use source aggregates available under the benchmark's documented nine-month observation period. Point-in-time verification at individual customer level is unavailable. Approved inputs are nonnegative integers at most 2^53−1, with a binary complaint flag. Nulls, extra columns, negative values and invalid complaint codes fail the contract. Unknown nonnegative tariff codes map to a dedicated indicator after engineering. No derived feature divides by another value.

| Feature | Formula and dependencies | Purpose and limitation |
|---|---|---|
| has_call_failure | int(call_failure > 0) | Unitless indicator separates any failure from intensity and retains source count separately. |
| complaint_with_failure | complains × int(call_failure > 0) | Unitless interaction for overlapping experience signals. Its value does not say that a complaint concerned a call failure. |
| log_seconds_of_use | log1p(seconds_of_use) | Unitless transform reduces skew of total call seconds. The source count is retained. |
| log_frequency_of_sms | log1p(frequency_of_sms) | Unitless transform reduces skew of SMS count. The source count is retained. |

FS01 contains eight approved fields. FS02 appends the two experience indicators. FS03 appends the two log transforms. Their raw-to-feature dimensions are 8, 10 and 10. After plan encoding, the linear and tree designs have 9, 11 and 11 columns. Tree design retains numeric scales. Linear design centers and scales numeric quantities. Both use a plan reference level and explicit unknown indicator. FS03 deliberately retains raw quantities and their transforms, so collinearity and regularization are considerations for Phase 3. No comparative performance has been measured.

The source eligibility policy is unchanged. Age and age group remain outside operational features. Demographic subgroup analysis is deferred. See [eligibility evidence](FEATURE_ELIGIBILITY.md) and [preprocessing](PREPROCESSING_PROTOCOL.md).
