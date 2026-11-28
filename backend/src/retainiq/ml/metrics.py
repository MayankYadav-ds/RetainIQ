"""Metrics, deployment decisions, and fixed-prediction group uncertainty."""

import math
import random
from collections import defaultdict

from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)


def divide(a: float, b: float) -> float:
    return a / b if b else 0.0


def confusion(y: list[int], decisions: list[int]) -> dict[str, float]:
    tn = fp = fn = tp = 0
    for target, pred in zip(y, decisions, strict=True):
        if target:
            tp += pred
            fn += 1 - pred
        else:
            fp += pred
            tn += 1 - pred
    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    specificity = divide(tn, tn + fp)
    return dict(
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
        precision=precision,
        recall=recall,
        specificity=specificity,
        accuracy=divide(tp + tn, len(y)),
        balanced_accuracy=(recall + specificity) / 2,
        f1=divide(2 * tp, 2 * tp + fp + fn),
        f2=divide(5 * tp, 5 * tp + fp + 4 * fn),
        mcc=divide(tp * tn - fp * fn, math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))),
        predicted_positive_rate=divide(tp + fp, len(y)),
    )


def brier(y: list[int], p: list[float]) -> float:
    return math.fsum((a - b) ** 2 for a, b in zip(y, p, strict=True)) / len(y)


def policy(
    y: list[int],
    p: list[float],
    objective: str = "f2",
    minimum: float = 0.5,
    fp_cost: float = 1.0,
    fn_cost: float = 1.0,
) -> tuple[float, list[dict[str, float]]]:
    sweep = [
        {"threshold": i / 100, **confusion(y, [int(q >= i / 100) for q in p])} for i in range(5, 96)
    ]
    if objective in ("f1", "f2"):
        score = lambda r: r[objective]
    elif objective == "recall_at_precision":
        sweep = [r for r in sweep if r["precision"] >= minimum and r["predicted_positive_rate"] > 0]
        score = lambda r: r["recall"]
    elif objective == "precision_at_recall":
        sweep = [r for r in sweep if r["recall"] >= minimum]
        score = lambda r: r["precision"]
    elif objective == "cost":
        score = lambda r: -fp_cost * r["fp"] - fn_cost * r["fn"]
    else:
        raise ValueError("unknown_threshold_objective")
    if not sweep:
        raise ValueError("no_feasible_threshold")
    return max(sweep, key=lambda r: (score(r), r["threshold"]))["threshold"], sweep


def ranking(y: list[int], raw: list[float], fraction: float) -> dict[str, float]:
    if not 0 < fraction <= 1:
        raise ValueError("invalid_capacity")
    k = math.ceil(len(y) * fraction)
    order = sorted(range(len(y)), key=lambda i: (-raw[i], i))
    hits = sum(y[i] for i in order[:k])
    return dict(
        k=k,
        fraction=fraction,
        precision=hits / k,
        recall=divide(hits, sum(y)),
        lift=divide(hits / k, sum(y) / len(y)),
    )


def evaluate(
    y: list[int], raw: list[float], p: list[float], decisions: list[int]
) -> dict[str, float | None]:
    if (
        not y
        or len(y) != len(raw)
        or len(y) != len(p)
        or any(v not in (0, 1) for v in y + decisions)
        or any(not 0 <= x <= 1 for x in raw + p)
    ):
        raise ValueError("invalid_evaluation_vectors")
    logloss = -math.fsum(
        math.log(max(1e-15, q if a else 1 - q)) for a, q in zip(y, p, strict=True)
    ) / len(y)
    return {
        **confusion(y, decisions),
        "n": len(y),
        "prevalence": sum(y) / len(y),
        "auc": float(roc_auc_score(y, raw)) if len(set(y)) == 2 else None,
        "ap": float(average_precision_score(y, raw)) if sum(y) else None,
        "brier": brier(y, p),
        "log_loss": logloss,
    }


def chart_data(y: list[int], raw: list[float], p: list[float]) -> dict[str, object]:
    bins: list[list[tuple[int, float]]] = [[] for _ in range(10)]
    for label, prob in zip(y, p, strict=True):
        bins[min(int(prob * 10), 9)].append((label, prob))
    cal = [
        dict(
            bin=i,
            count=len(cell),
            predicted=divide(sum(q for _, q in cell), len(cell)),
            observed=divide(sum(a for a, _ in cell), len(cell)),
        )
        for i, cell in enumerate(bins)
        if cell
    ]
    roc: list[list[float]] = []
    pr: list[list[float]] = []
    if len(set(y)) == 2:
        fpr, tpr, _ = roc_curve(y, raw)
        precision, recall, _ = precision_recall_curve(y, raw)
        for target, x, z in ((roc, fpr, tpr), (pr, recall, precision)):
            indexes = sorted({round(i * (len(x) - 1) / 64) for i in range(65)})
            target.extend([[float(x[i]), float(z[i])] for i in indexes])
    return {
        "roc": roc,
        "pr": pr,
        "calibration": cal,
        "ece": sum(c["count"] * abs(c["predicted"] - c["observed"]) for c in cal) / len(y),
        "ranking": [ranking(y, raw, i / 100) for i in (5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)],
    }


def bootstrap(
    y: list[int],
    raw: list[float],
    p: list[float],
    pred: list[int],
    groups: list[str],
    repeats: int = 200,
    seed: int = 20261127,
) -> dict[str, object]:
    clusters: dict[str, list[int]] = defaultdict(list)
    for i, g in enumerate(groups):
        clusters[g].append(i)
    rng = random.Random(seed)
    draws: dict[str, list[float]] = defaultdict(list)
    for _ in range(repeats):
        ix = [i for cl in rng.choices(list(clusters.values()), k=len(clusters)) for i in cl]
        a = [y[i] for i in ix]
        if len(set(a)) != 2:
            continue
        m = evaluate(a, [raw[i] for i in ix], [p[i] for i in ix], [pred[i] for i in ix])
        for name in ("ap", "auc", "brier", "recall", "precision"):
            value = m[name]
            if value is not None:
                draws[name].append(value)
    bounds = {
        k: [sorted(v)[round((len(v) - 1) * q)] for q in (0.025, 0.975)] for k, v in draws.items()
    }
    return {"repetitions": repeats, "valid": len(draws["ap"]), "seed": seed, "intervals": bounds}
