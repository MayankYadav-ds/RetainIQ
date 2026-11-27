# Feature eligibility · UCI schema v1

The default projection is an explicit allowlist. Decisions use source semantics and unconditional engineering checks. No full-dataset feature-to-label association was used. For each approved field below, the publisher's nine-month aggregate description is moderate evidence of availability by the conceptual cutoff. Row-level availability remains unverified. All eight stay approved only for the snapshot benchmark; transfers to operational billing systems need fresh timestamp validation.

| Predictor(s) | Decision and potential leakage | Default |
|---|---|---|
| call_failure, complains | Failed-call count and complaint flag describe prior service experience. Late-entered complaints or backfilled call records could change cutoff availability. | Yes |
| seconds_of_use, frequency_of_use, frequency_of_sms, distinct_called_numbers | Reported aggregate usage. Post-cutoff aggregation or later corrections would leak future activity; source defines the period, no event timestamps exist to re-audit it. | Yes |
| subscription_length | Tenure at the described snapshot. A tenure measured at churn or last contact would leak follow-up. Do not use it to derive survival labels. | Yes |
| tariff_plan | Subscription type under the source period. A later renewal-plan update would leak outcome-period decisions. Preserve categorical semantics. | Yes |
| charge_amount | Conditionally approved ordinal band. Seven observations are 10 while the definition ends at 9. Resolve coding with the publisher before operational inclusion. Actual billing revenue is unknown. | No |
| status | Excluded. Active/non-active can encode an outcome proxy. The general observation-window statement does not resolve the precise update time or relationship to the churn definition. | No |
| customer_value | Requires further evidence. UCI calls it a calculated value. Its formula, units and input cutoffs are undisclosed. Future activity may enter the score. No evidence supports treating it as CLV, rupees or margin. | No |
| age, age_group | Excluded from operational features. Demographic and overlapping in the actual archive, useful for appropriately privacy-controlled subgroup auditing. Exact age measurement is uncertain. | No |

The binary churn field is a label. The generated record_id traces source position. Neither enters the default feature projection; no real account identifier exists. The runtime policy lives in backend/src/retainiq/data/contract.py. Any eligibility change requires review and a pipeline version increment.
