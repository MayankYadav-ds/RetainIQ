"""Independent arithmetic over local, already-frozen benchmark and receipt artifacts."""

import argparse
import json
import math
from collections import Counter
from itertools import groupby
from pathlib import Path


def check(y, p, raw, pred, m):
    n = len(y)
    c = Counter(zip(y, pred, strict=True))
    tp, fp, fn, tn = [c[k] for k in ((1, 1), (0, 1), (1, 0), (0, 0))]
    assert all(
        m[k] == v
        for k, v in zip(("tp", "fp", "fn", "tn"), (tp, fp, fn, tn), strict=True)
    )
    rat = lambda a, b: a / b if b else 0.0
    vals = {
        "precision": rat(tp, tp + fp),
        "recall": rat(tp, tp + fn),
        "f1": rat(2 * tp, 2 * tp + fp + fn),
        "accuracy": (tp + tn) / n,
        "brier": sum((a - b) ** 2 for a, b in zip(y, p, strict=True)) / n,
    }
    pairs = sorted(zip(raw, y, strict=True), reverse=True)
    hits = total = lower_neg_auc = 0
    ap = 0.0
    positives = sum(y)
    negatives = n - positives
    for _, group in groupby(pairs, key=lambda pair: pair[0]):
        labels = [b for _, b in group]
        pos = sum(labels)
        neg = len(labels) - pos
        hits += pos
        total += len(labels)
        ap += rat(pos, positives) * hits / total
        lower_neg_auc += pos * (negatives - (total - hits) + neg / 2)
    vals.update(ap=ap, auc=rat(lower_neg_auc, positives * negatives))
    assert all(math.isclose(m[k], v, abs_tol=1e-10) for k, v in vals.items())


def charts(y, p, raw, aggregates):
    for cell in aggregates["calibration"]:
        subset = [
            (a, b)
            for a, b in zip(y, p, strict=True)
            if min(math.floor(10 * b), 9) == cell["bin"]
        ]
        assert len(subset) == cell["count"]
        assert math.isclose(
            sum(a for a, _ in subset) / len(subset), cell["observed"], abs_tol=1e-10
        )
    assert sum(b["count"] for b in aggregates["calibration"]) == len(y)
    order = sorted(range(len(y)), key=lambda i: -raw[i])
    for rank in aggregates["ranking"]:
        n = math.ceil(rank["fraction"] * len(y))
        hits = sum(y[j] for j in order[:n])
        assert n == rank["k"] and math.isclose(
            hits / n, rank["precision"], abs_tol=1e-10
        )
        assert math.isclose((hits / n) / (sum(y) / len(y)), rank["lift"], abs_tol=1e-10)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiment", required=True)
    p.add_argument("--root", type=Path, default=Path("data"))
    p.add_argument("--receipt", help="Optional existing receipt ID")
    a = p.parse_args()
    folder = a.root / "ml" / "experiments" / a.experiment
    summary = json.loads((folder / "summary.json").read_bytes())
    oof = json.loads((folder / "oof.json").read_bytes())
    search = json.loads((folder / "search.json").read_bytes())
    for family in summary["leaderboard"]:
        name = family["family"]
        if family["status"] != "complete":
            continue
        d = oof[name]
        check(d["y"], d["probability"], d["raw"], d["decision"], family["metrics"])
        assert len(set(d["ids"])) == len(d["y"])
        grouped = {}
        for group, fold in zip(d["groups"], d["folds"], strict=True):
            assert grouped.setdefault(group, fold) == fold
        for fold, fit in enumerate(search[name]):
            ids = fit["role_membership"]
            tr, ca, pol = [set(ids[k]) for k in ("core", "calibration", "policy")]
            outer = {r for r, k in zip(d["ids"], d["folds"], strict=True) if k == fold}
            assert not (tr & ca or tr & pol or ca & pol or (tr | ca | pol) & outer)
            assert tr | ca | pol | outer == set(d["ids"]) and len(ids["inner"]) == len(
                tr
            )
            for i, k in enumerate(d["folds"]):
                if k == fold:
                    assert d["decision"][i] == int(
                        d["probability"][i] >= fit["threshold"]
                    )
    real = [row for row in summary["leaderboard"][2:] if row["status"] == "complete"]
    best = max(r["metrics"]["ap"] for r in real)
    close = [r for r in real if best - r["metrics"]["ap"] <= 0.002]
    brier = min(r["metrics"]["brier"] for r in close)
    expected = next(
        r["family"] for r in close if r["metrics"]["brier"] - brier <= 0.001
    )
    assert expected == summary["selected"]
    r = oof[expected]
    charts(r["y"], r["probability"], r["raw"], summary["development"])
    print(
        "Verified complete OOF rows, nested roles, champion, metrics, calibration and ranking."
    )
    if a.receipt:
        for path in (a.root / "ml" / "evaluations").glob("*/receipt.json"):
            entry = json.loads(path.read_bytes())
            if entry["receipt"] != a.receipt:
                continue
            c = entry["content"]
            d = json.loads((path.parent / "local-predictions.json").read_bytes())
            check(d["y"], d["p"], d["raw"], d["decisions"], c["metrics"])
            assert [int(x >= c["threshold"]) for x in d["p"]] == d["decisions"]
            charts(d["y"], d["p"], d["raw"], c["charts"])
            print("Verified the existing final evaluation without estimator refit.")
            return
        raise ValueError("receipt_missing")


if __name__ == "__main__":
    main()
