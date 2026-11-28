# Partition integrity

Dataset version 461e2bba687bc6e8f52284c9. The original manifest, normalized records and both partition file hashes were verified. The original split remains 2,520 development and 630 final holdout. The isolated auditor reads ordinals from each role file and selects only source predictor keys from the full snapshot. JSON decoding can receive a label field as part of the format, but the auditor never selects, compares, persists or uses that field. Ordinary analysis uses the existing verified development reader. Its checksum checks treat the final file as opaque bytes.

| Check | Result |
|---|---:|
| Shared 13-predictor groups | 0 |
| Shared approved eight-predictor groups | 16 |
| Affected development observations | 40 |
| Affected holdout observations | 78 |
| Eligible development observations | 2,480 |

Policy quarantine-projected-v1 excludes every affected development ordinal, regardless of label, before folds or target-conditioned analysis. Neither source partition is rewritten. This is a conservative policy about exact projected vectors. Source identity and independence cannot be established. The model input variants retain all eight original predictors and append features. The production code checks for new projected collisions on eligible development observations. The encodings retain distinct supported tariff categories and scaling uses positive scales. No holdout transformation informed feature selection.

Only fixed aggregate results may be exposed. Filesystem administrators can still read the source store. Final evaluation must use the original holdout and the frozen policy. See [operating instructions](FEATURE_ENGINEERING.md).
