"""Independent aggregate and feature verification using development inputs only."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def check(root: Path, version: str, view: str) -> None:
    dataset = "uci_iranian_churn"
    source = root / "processed" / dataset / version
    area = root / "analysis" / dataset / version / view
    report = json.loads((area / "report.json").read_bytes())
    reference = json.loads((area / "manifest.json").read_bytes())["reference"]
    assert (
        hashlib.sha256((source / "holdout.jsonl").read_bytes()).hexdigest()
        == reference["split"]["holdout.jsonl"]
    )
    features = json.loads((area / "features.json").read_bytes())
    membership = json.loads((area / "folds.json").read_bytes())["members"]
    originals = {
        a["record_id"]: a
        for a in map(
            json.loads, (source / "development.jsonl").read_bytes().splitlines()
        )
    }
    ids, folds = zip(*membership, strict=True)
    assert len(ids) == len(set(ids)) == report["eligible"]
    rows = [originals[i]["features"] for i in ids]
    y = [originals[i]["target"] for i in ids]
    assert (
        sum(y) == report["positives"]
        and sum(a["target"] for a in originals.values()) == report["before_positive"]
    )
    assert len(originals) - len(rows) == report["audit"]["affected_dev"]
    groups = {}
    for row, f in zip(rows, folds, strict=True):
        assert groups.setdefault(tuple(sorted(row.items())), f) == f
    counts = Counter(zip(folds, y, strict=True))
    assert [[counts[i, 0], counts[i, 1]] for i in range(5)] == report["folds"]

    def eq(a: float, b: float) -> None:
        assert math.isclose(a, b, abs_tol=1e-10, rel_tol=1e-10)

    for d in report["distributions"]:
        values = sorted(r[d["name"]] for r in rows)
        assert len(values) == d["n"] and sum(v is None for v in values) == d["missing"]
        if "mean" not in d["summary"]:
            assert Counter(map(str, values)) == {
                c["label"]: c["count"] for c in d["cells"]
            }
            continue
        n = len(values)
        eq(sum(values) / n, d["summary"]["mean"])
        eq((values[(n - 1) // 2] + values[n // 2]) / 2, d["summary"]["median"])
        for p, label in ((0.05, "p05"), (0.95, "p95")):
            at = (n - 1) * p
            eq(
                values[math.floor(at)] * (1 - at % 1)
                + values[math.ceil(at)] * (at % 1),
                d["summary"][label],
            )
    for assoc in report["associations"]:
        x = [r[assoc["left"]] for r in rows]
        z = [r[assoc["right"]] for r in rows]
        n = len(x)
        numerator = n * sum(a * b for a, b in zip(x, z, strict=True)) - sum(x) * sum(z)
        denominator = math.sqrt(
            (n * sum(a * a for a in x) - sum(x) ** 2)
            * (n * sum(b * b for b in z) - sum(z) ** 2)
        )
        eq(numerator / denominator, assoc["r"])
    for fs, matrix in features["values"].items():
        names = features["feature_names"][fs]
        for row, actual in zip(rows, matrix, strict=True):
            expected = dict(row)
            expected.update(
                has_call_failure=int(row["call_failure"] > 0),
                complaint_with_failure=int(row["call_failure"] > 0) * row["complains"],
                log_seconds_of_use=math.log(1 + row["seconds_of_use"]),
                log_frequency_of_sms=math.log(1 + row["frequency_of_sms"]),
            )
            for a, name in zip(actual, names, strict=True):
                eq(a, expected[name])
    print(
        f"Reconciled {len(rows)} eligible rows, {len(groups)} groups, all five folds and three feature matrices."
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True)
    p.add_argument("--view", required=True)
    p.add_argument("--root", type=Path, default=Path("data"))
    args = p.parse_args()
    check(args.root, args.version, args.view)
