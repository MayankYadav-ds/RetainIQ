"""Frozen search and policy constants. Change the revision for a new protocol."""

from retainiq.analysis.features import SETS, fingerprint
from retainiq.data.contract import SEED, digest, encoded

VERSION = "snapshot-nested-v1"
DATASET = "461e2bba687bc6e8f52284c9"
VIEW = "136a09a0f2ec6a66bf3ca6f3"
RECORDS = "db4bbb548cc23ae66d5d66ab75ab04f49549ac33704f0b665e04b0dd2dd18f53"
HOLDOUT = "e9509c84629e8e03827d8d27823216c9a890b86cc589f7afa77b1265584ba63a"
FOLDS = "82a46397d506eca6252994b2999fb2013a01579aa5c49ab49fa53abcd38bd776"
GRIDS = {
    "logistic": [{"C": 0.5}, {"C": 2.0, "class_weight": "balanced"}],
    "tree": [
        {"max_depth": 3, "min_samples_leaf": 12},
        {"max_depth": 5, "min_samples_leaf": 18, "class_weight": "balanced"},
    ],
    "forest": [
        {"n_estimators": 60, "max_depth": 7, "min_samples_leaf": 5},
        {"n_estimators": 60, "max_depth": 10, "min_samples_leaf": 5, "class_weight": "balanced"},
    ],
    "extra_trees": [
        {"n_estimators": 60, "max_depth": 7, "min_samples_leaf": 5},
        {"n_estimators": 60, "max_depth": 10, "min_samples_leaf": 5, "class_weight": "balanced"},
    ],
    "hist_gradient": [
        {"max_iter": 70, "max_leaf_nodes": 7},
        {"max_iter": 100, "max_leaf_nodes": 15, "class_weight": "balanced"},
    ],
    "xgboost": [
        {"n_estimators": 65, "max_depth": 3},
        {"n_estimators": 90, "max_depth": 4, "scale_pos_weight": 2.0},
    ],
    "lightgbm": [
        {"n_estimators": 65, "num_leaves": 7},
        {"n_estimators": 90, "num_leaves": 15, "scale_pos_weight": 2.0},
    ],
}
BANDS = {"low": 0.0, "moderate": 0.1, "high": 0.25, "critical": 0.5}
SPEC = {
    "revision": VERSION,
    "dataset": DATASET,
    "view": VIEW,
    "records": RECORDS,
    "holdout": HOLDOUT,
    "folds": FOLDS,
    "quarantine": "quarantine-projected-v1",
    "features": {s: fingerprint(s) for s in SETS},
    "seed": SEED,
    "grids": GRIDS,
    "threads": 1,
    "outer_folds": 5,
    "inner_folds": 3,
    "calibration": ["none", "sigmoid", "isotonic"],
    "isotonic_min_per_class": 30,
    "threshold": "max_f2_over_0.05_to_0.95_steps_0.01_ties_higher",
    "selection": "raw pooled OOF average precision within 0.002, then calibrated Brier within 0.001, then fixed complexity order",
    "calibration_selection": "policy-set Brier; ties within 0.0001 prefer none, then sigmoid, then isotonic",
    "bootstrap_replicates": 200,
    "risk_bands": BANDS,
    "failure": "record type and skip incomplete procedure",
    "size_limit": 8000000,
    "promotion": "complete OOF, safe round-trip, finite predictions and completed final receipt; no accuracy floor",
}
PROTOCOL_SHA = digest(encoded(SPEC))
