# UCI development benchmark

Experiment 6dfabb46b6c290694b53914a. All seven candidate families and two references completed on Windows x64. All learned families evaluated 30 feature/parameter configurations across five outer folds (90 inner fits per family). The model choice rests on pooled raw OOF average precision. Probability errors use calibrated probabilities. Classification metrics use each outer fold's frozen threshold. Average precision is the step-weighted precision–recall measure. It is distinct from trapezoidal PR area.

| Family | Feature sets by fold | ROC-AUC | AP | Brier | Precision | Recall | F1 | Accuracy | Fold AP SD | Seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | Baseline | 0.5000 | 0.1500 | 0.1500 | 0.0000 | 0.0000 | 0.0000 | 0.8500 | 0.0008 | 0.011 |
| prevalence | Baseline | 0.4985 | 0.1496 | 0.1275 | 0.0000 | 0.0000 | 0.0000 | 0.8500 | 0.0008 | 0.011 |
| logistic | FS01, FS01, FS03, FS03, FS01 | 0.9178 | 0.7452 | 0.0687 | 0.4035 | 0.8710 | 0.5515 | 0.7875 | 0.0205 | 2.415 |
| tree | FS01, FS01, FS01, FS01, FS01 | 0.9128 | 0.7275 | 0.0674 | 0.3196 | 0.8978 | 0.4714 | 0.6980 | 0.0424 | 2.178 |
| forest | FS03, FS01, FS01, FS01, FS03 | 0.9541 | 0.8355 | 0.0523 | 0.5170 | 0.9005 | 0.6569 | 0.8589 | 0.0445 | 7.207 |
| extra_trees | FS03, FS01, FS01, FS03, FS03 | 0.9516 | 0.8211 | 0.0592 | 0.4256 | 0.9462 | 0.5872 | 0.8004 | 0.0329 | 5.377 |
| hist_gradient | FS01, FS01, FS01, FS01, FS01 | 0.9718 | 0.8922 | 0.0440 | 0.5969 | 0.9355 | 0.7288 | 0.8956 | 0.0323 | 5.680 |
| xgboost | FS01, FS01, FS01, FS01, FS01 | 0.9699 | 0.8847 | 0.0448 | 0.5661 | 0.9435 | 0.7077 | 0.8831 | 0.0318 | 3.794 |
| lightgbm | FS01, FS01, FS01, FS01, FS01 | 0.9645 | 0.8677 | 0.0478 | 0.5518 | 0.9167 | 0.6889 | 0.8758 | 0.0215 | 3.135 |

The pooled prevalence reference uses fold-specific training prevalence. Tiny differences across folds can create an artificial ranking. Its within-fold scores are constant. Stable source ordering resolves ranking ties.

All seven learned families compared unweighted and weighted options. FS01 was selected in all five champion folds. FS03 was selected in some logistic and ensemble folds. No engineered feature set was declared superior. The champion's pooled AP of 0.8922 exceeded the next family's 0.8847 by more than the 0.002 tie interval.

The benchmark took 29.845 s. A second isolated development run took 29.563 s and reproduced the OOF predictions byte for byte. Windows peak process working set on that repeat was 274,685,952 bytes (262.0 MiB). AMD Ryzen 7 7840HS x64, 8 physical cores, one training thread, CPU. Times include selection and validation for each family. The final training procedure took 1.508 s. The verified artifact is 589,194 bytes. Warm in-process inference including input transformation and calibration measured 2.17 ms median / 2.35 ms empirical p95 for one record and 4.21 ms / 4.80 ms for a 100-record batch (60 measured calls per size after 8 warmups, excludes HTTP).

Use retainiq-ml compare with --detailed for per-family curve, ranking and reliability evidence. Per-fold metrics, every attempted configuration and private membership evidence are stored locally. Read the executable protocol and the calibration report for scope.
