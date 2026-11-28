# Development exploratory analysis

Dataset 461e2bba687bc6e8f52284c9, view 136a09a0f2ec6a66bf3ca6f3. All target-conditioned results use the 2,480 eligible development observations. Churn prevalence moved from 396/2,520 (15.71%) to 372/2,480 (15.00%) under the frozen quarantine policy. The eligible class ratio is 2,108:372, about 5.67:1. An always-non-churn rule would classify 85% correctly and recall none of the churn cases. This is a class-distribution calculation.

The approved fields have zero missing values and none is constant. Invalid or missing input fails the schema. No observations were dropped for the outlier flags. The median usage is 3,137.5 seconds, median calls 56 and median SMS messages 23. Tukey 1.5-IQR fences flagged 279 SMS counts, 187 tenure values, 170 usage-seconds values, 109 call counts, 73 distinct-destination counts and 54 failure counts. These flags describe tail behavior only.

Complaint status showed 170/208 churn (81.73%) among observations with a complaint and 202/2,272 (8.89%) among those without. The categorical report includes marginal Wilson intervals. Tariff class-conditionals are suppressed because at least one class-by-category cell has fewer than ten observations. Categorical codes are treated as nominal categories.

Usage seconds showed a standardized mean difference of -1.043 (churn minus non-churn), call count -1.016, distinct destinations -0.830 and SMS count -0.769. The approximate unadjusted usage-seconds mean difference interval is [-3,607, -3,131] seconds. Numeric feature pairs with the strongest observed correlations were total seconds versus call count (Pearson r = 0.944), call count versus destinations (r = 0.719) and seconds versus destinations (r = 0.660). Consider this redundancy in future estimator comparisons. The candidate sets have no exact duplicate or constant columns on the eligible sample.

See [statistical methods](STATISTICAL_ANALYSIS.md) and [reproduction commands](FEATURE_ENGINEERING.md).
