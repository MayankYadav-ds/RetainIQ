"""Persist local OOF rows separately from bounded aggregate benchmark evidence."""

import json
import statistics
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from threadpoolctl import threadpool_limits

from retainiq.analysis.integrity import key
from retainiq.data.acquire import publish_dir, staging
from retainiq.data.contract import APPROVED, digest, encoded, file_sha

from .cohort import Cohort, subset
from .metrics import bootstrap, chart_data, evaluate, policy
from .protocol import GRIDS, PROTOCOL_SHA
from .train import train


def dependencies() -> dict[str, str]:
    out = {}
    for package in (
        "numpy",
        "scipy",
        "scikit-learn",
        "skops",
        "threadpoolctl",
        "xgboost",
        "lightgbm",
    ):
        try:
            out[package] = version(package)
        except PackageNotFoundError:
            out[package] = "absent"
    return out


def identifier(value: str) -> str:
    if len(value) != 24 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("invalid_identifier")
    return value


def load_benchmark(root: Path, experiment: str) -> tuple[Path, dict[str, Any]]:
    folder = root / "ml" / "experiments" / identifier(experiment)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    if (
        manifest["protocol"] != PROTOCOL_SHA
        or digest(encoded(manifest["identity"]))[:24] != experiment
    ):
        raise ValueError("experiment_identity")
    for name in ("summary.json", "oof.json", "search.json"):
        if file_sha(folder / name) != manifest["checksums"][name]:
            raise ValueError("benchmark_corruption")
    summary: dict[str, Any] = json.loads((folder / "summary.json").read_bytes())
    if summary["experiment"] != experiment:
        raise ValueError("benchmark_reference")
    return folder, summary


def champion(leaders: list[dict[str, Any]]) -> str:
    completed = [r for r in leaders if r["status"] == "complete" and r["family"] in GRIDS]
    if not completed:
        raise ValueError("no_completed_model")
    ceiling = max(r["metrics"]["ap"] for r in completed)
    eligible = [r for r in completed if r["metrics"]["ap"] >= ceiling - 0.002]
    floor = min(r["metrics"]["brier"] for r in eligible)
    return next(
        family
        for family in GRIDS
        if any(r["family"] == family and r["metrics"]["brier"] <= floor + 0.001 for r in eligible)
    )


def benchmark(root: Path, c: Cohort, quick: bool = False) -> dict[str, Any]:
    start = time.perf_counter()
    ref = {
        "cohort": c.reference,
        "protocol": PROTOCOL_SHA,
        "dependencies": dependencies(),
        "quick": quick,
    }
    exp = digest(encoded(ref))[:24]
    dest = root / "ml" / "experiments" / exp
    if dest.exists():
        return load_benchmark(root, exp)[1]
    data = c.data
    groups = [key(r, APPROVED) for r in data.x]
    board = []
    oof: dict[str, dict[str, Any]] = {}
    evidence = {}
    for family in ("majority", "prevalence", *(["logistic"] if quick else GRIDS)):
        raw = [0.0] * len(data.y)
        probs = raw.copy()
        decision = [0] * len(raw)
        fold_evidence = []
        folds = []
        started = time.perf_counter()
        try:
            for fold in range(5):
                train_ix = [i for i, f in enumerate(c.outer) if f != fold]
                test_ix = [i for i, f in enumerate(c.outer) if f == fold]
                training = subset(data, train_ix)
                validation = subset(data, test_ix)
                if family in ("majority", "prevalence"):
                    r = [0.0 if family == "majority" else sum(training.y) / len(training.y)] * len(
                        test_ix
                    )
                    p = r
                    threshold = 0.5
                else:
                    fitted = train(training, family, fold, quick)
                    with threadpool_limits(limits=1):
                        r = fitted.base.scores(validation.x)
                    p = [fitted.calibration.apply(x) for x in r]
                    threshold = fitted.threshold
                    fold_evidence.append(fitted.evidence)
                d = [int(x >= threshold) for x in p]
                folds.append(evaluate(validation.y, r, p, d))
                for i, rr, pp, dd in zip(test_ix, r, p, d, strict=True):
                    raw[i], probs[i], decision[i] = rr, pp, dd
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            board.append({"family": family, "status": "failed", "failure": type(exc).__name__})
            evidence[family] = fold_evidence
            continue
        record = {
            "family": family,
            "status": "complete",
            "metrics": evaluate(data.y, raw, probs, decision),
            "folds": folds,
            "ap_sd": statistics.stdev(float(m["ap"] or 0) for m in folds),
            "seconds": time.perf_counter() - started,
            "features": [e["choice"]["fs"] for e in fold_evidence],
            "calibration": [e["calibration"] for e in fold_evidence],
        }
        board.append(record)
        oof[family] = {
            "y": data.y,
            "raw": raw,
            "probability": probs,
            "decision": decision,
            "groups": groups,
            "folds": c.outer,
            "ids": data.ids,
        }
        evidence[family] = fold_evidence
    selected = champion(board)
    winner = oof[selected]
    _, sweep = policy(data.y, winner["probability"])
    aggregate = {
        "experiment": exp,
        "cohort": c.reference,
        "protocol": PROTOCOL_SHA,
        "quick": quick,
        "leaderboard": board,
        "selected": selected,
        "seconds": time.perf_counter() - start,
        "calibration_choices": [e["brier"] for e in evidence[selected]],
        "development": chart_data(data.y, winner["raw"], winner["probability"]),
        "threshold_sweep": sweep,
        "uncertainty": bootstrap(
            data.y,
            winner["raw"],
            winner["probability"],
            winner["decision"],
            groups,
            repeats=20 if quick else 200,
        ),
    }
    with staging(root) as temp:
        folder = temp / "experiment"
        folder.mkdir()
        for name, obj in (
            ("summary.json", aggregate),
            ("oof.json", oof),
            ("search.json", evidence),
        ):
            (folder / name).write_bytes(encoded(obj))
        manifest = {
            "protocol": PROTOCOL_SHA,
            "identity": ref,
            "checksums": {
                n: file_sha(folder / n) for n in ("summary.json", "oof.json", "search.json")
            },
        }
        (folder / "manifest.json").write_bytes(encoded(manifest))
        publish_dir(folder, dest)
    return load_benchmark(root, exp)[1]
