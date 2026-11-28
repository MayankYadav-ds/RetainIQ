# Frozen final holdout evaluation

Model 2234d0279bb9bd18d77c27b3. Artifact SHA-256 02c3bfae7ed9cd2f8345f9e839118f1d5d401f3562bbe7d7dff91ec7f5fe8344. Freeze digest c84127d76d2e005eb224f857b1386bbb7be9668b114ba5390278aa796c15a2f2. Receipt 6f0e95d28d791f4d703cdac4743432f762805a0374f24569bbb878f33f034b79.

Evaluation timestamp 2026-11-28T14:34:50.413821+00:00. The original protected holdout hash e9509c84629e8e03827d8d27823216c9a890b86cc589f7afa77b1265584ba63a was verified before and after evaluation. Exactly 630 records and 99 positive labels (15.71%). The one-shot access marker remains in the local store. No choice changed after opening the holdout.

| Metric | Result |
|---|---:|
| accuracy | 0.901587 |
| balanced_accuracy | 0.925184 |
| auc | 0.959767 |
| ap | 0.806097 |
| precision | 0.620915 |
| recall | 0.959596 |
| f1 | 0.753968 |
| f2 | 0.865209 |
| brier | 0.057523 |
| log_loss | 0.177680 |
| specificity | 0.890772 |
| mcc | 0.721717 |

Confusion counts at p ≥ 0.28: TN 473, FP 58, FN 4, TP 95. ECE is 0.047140 with ten equal-width bins. The constant development-prevalence prediction has AP 0.157143 and Brier 0.132500 (computed from the verified receipt below).

| Review fraction | K | Precision | Recall | Lift |
|---|---:|---:|---:|---:|
| 5% | 32 | 1.0000 | 0.3232 | 6.364 |
| 10% | 63 | 0.7937 | 0.5051 | 5.051 |
| 20% | 126 | 0.6587 | 0.8384 | 4.192 |

Group bootstrap, 200 of 200 valid draws and seed 20261127. Approximate 95% intervals:
- ap: [0.6794, 0.9014]
- auc: [0.9365, 0.9794]
- brier: [0.0387, 0.0762]
- precision: [0.5361, 0.7459]
- recall: [0.9178, 0.9909]

These intervals condition on the frozen model and observed sample. Grouping by feature vector does not establish customer independence. No other learned candidate was evaluated on final labels. Independent arithmetic verified the saved scores and threshold decisions without additional model fits.
