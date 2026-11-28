"""Serial nested search with disjoint development-only probability policy roles."""

import math
import time
from dataclasses import dataclass
from typing import Any

from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

from retainiq.analysis.features import SETS, FoldState, fit_subset
from retainiq.analysis.view import View, folds
from retainiq.data.contract import SEED, digest, encoded

from .cohort import subset
from .metrics import brier, policy
from .protocol import GRIDS


def make(family: str, params: dict[str, Any]) -> Any:
    constructors = {
        "logistic": LogisticRegression,
        "tree": DecisionTreeClassifier,
        "forest": RandomForestClassifier,
        "extra_trees": ExtraTreesClassifier,
        "hist_gradient": HistGradientBoostingClassifier,
    }
    config = {"random_state": SEED, **params}
    if family in ("forest", "extra_trees"):
        config["n_jobs"] = 1
    if family == "hist_gradient":
        config["early_stopping"] = False
    if family == "logistic":
        config["max_iter"] = 500
    if family == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(n_jobs=1, tree_method="hist", verbosity=0, **config)
    if family == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
            n_jobs=1, deterministic=True, force_col_wise=True, verbosity=-1, **config
        )
    return constructors[family](**config)


@dataclass
class Fitted:
    estimator: Any
    state: FoldState
    membership: str

    def scores(self, rows: list[dict[str, int]]) -> list[float]:
        design = [self.state.apply(row) for row in rows]
        if hasattr(self.estimator, "feature_name_"):
            from numpy import asarray

            arr = self.estimator.booster_.predict(asarray(design), num_threads=1)
        else:
            arr = self.estimator.predict_proba(design)[:, 1]
        result = [float(p) for p in arr]
        if len(result) != len(rows) or any(not 0 <= p <= 1 for p in result):
            raise ValueError("invalid_estimator_scores")
        return result


def fit_base(v: View, family: str, fs: str, params: dict[str, Any], fold: int) -> Fitted:
    state = fit_subset(v.x, fs, "linear" if family == "logistic" else "tree", fold)
    model = make(family, params)
    model.fit([state.apply(x) for x in v.x], v.y)
    return Fitted(model, state, digest(encoded(v.ids)))


def sigmoid(z: float) -> float:
    e = math.exp(-abs(z))
    return 1 / (1 + e) if z >= 0 else e / (1 + e)


def logit(p: float) -> float:
    clipped = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(clipped / (1 - clipped))


@dataclass(frozen=True)
class Calibration:
    method: str
    x: list[float]
    y: list[float]

    def apply(self, p: float) -> float:
        if self.method == "none":
            return p
        if self.method == "sigmoid":
            return sigmoid(self.x[0] * logit(p) + self.y[0])
        from bisect import bisect_right

        i = bisect_right(self.x, p)
        if i == 0:
            return self.y[0]
        if i == len(self.x):
            return self.y[-1]
        return self.y[i - 1] + (self.y[i] - self.y[i - 1]) * (p - self.x[i - 1]) / (
            self.x[i] - self.x[i - 1]
        )


def calibrators(r: list[float], y: list[int]) -> list[Calibration]:
    lr = LogisticRegression(C=1.0).fit([[logit(p)] for p in r], y)
    out = [
        Calibration("none", [], []),
        Calibration("sigmoid", [float(lr.coef_[0, 0])], [float(lr.intercept_[0])]),
    ]
    if min(y.count(0), y.count(1)) >= 30:
        iso = IsotonicRegression(out_of_bounds="clip").fit(r, y)
        out.append(Calibration("isotonic", iso.X_thresholds_.tolist(), iso.y_thresholds_.tolist()))
    return out


@dataclass
class Procedure:
    base: Fitted
    calibration: Calibration
    threshold: float
    evidence: dict[str, Any]


def train(v: View, family: str, outer: int, quick: bool = False) -> Procedure:
    roles = folds(v, 4 if quick else 5)
    core = subset(v, [i for i, f in enumerate(roles) if f >= 2])
    cal = subset(v, [i for i, f in enumerate(roles) if f == 0])
    decision = subset(v, [i for i, f in enumerate(roles) if f == 1])
    k = 2 if quick else 3
    inner = folds(core, k)
    candidates: list[dict[str, Any]] = []
    start = time.perf_counter()
    with threadpool_limits(limits=1):
        for fs in ["FS01"] if quick else SETS:
            for params in GRIDS[family][:1] if quick else GRIDS[family]:
                scores = []
                try:
                    for i in range(k):
                        itr = subset(core, [j for j, k in enumerate(inner) if k != i])
                        iva = subset(core, [j for j, k in enumerate(inner) if k == i])
                        raw = fit_base(itr, family, fs, params, i).scores(iva.x)
                        scores.append(float(average_precision_score(iva.y, raw)))
                    candidates.append({"fs": fs, "parameters": params, "ap": sum(scores) / k})
                except (ValueError, RuntimeError, OSError, ImportError) as exc:
                    candidates.append({"fs": fs, "parameters": params, "error": type(exc).__name__})
        complete = [c for c in candidates if "ap" in c]
        if not complete:
            raise RuntimeError("no_candidate_completed")
        best = max(float(c["ap"]) for c in complete)
        choice = next(c for c in complete if float(c["ap"]) >= best - 0.002)
        config: dict[str, Any] = choice["parameters"]
        feature = str(choice["fs"])
        base = fit_base(core, family, feature, config, outer)
        methods = calibrators(base.scores(cal.x), cal.y)
        policy_raw = base.scores(decision.x)
        scores_by_method = {
            c.method: brier(decision.y, [c.apply(p) for p in policy_raw]) for c in methods
        }
        method = next(
            c
            for c in methods
            if scores_by_method[c.method] <= min(scores_by_method.values()) + 0.0001
        )
        threshold, _ = policy(decision.y, [method.apply(p) for p in policy_raw])
        refit = fit_base(v, family, feature, config, outer)
    evidence = {
        "candidates": candidates,
        "choice": choice,
        "role_counts": {
            name: [count.y.count(0), count.y.count(1)]
            for name, count in (("core", core), ("calibration", cal), ("policy", decision))
        },
        "role_membership": {
            "core": core.ids,
            "calibration": cal.ids,
            "policy": decision.ids,
            "inner": inner,
        },
        "brier": scores_by_method,
        "threshold": threshold,
        "calibration": method.method,
        "seconds": time.perf_counter() - start,
    }
    return Procedure(refit, method, threshold, evidence)
