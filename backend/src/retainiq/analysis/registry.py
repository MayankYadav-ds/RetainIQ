"""Immutable development analysis artifacts."""

import json
import math
import platform
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from retainiq.data.acquire import publish_dir, staging
from retainiq.data.contract import APPROVED, SEED, digest, encoded, file_sha
from retainiq.data.registry import read_manifest

from .features import CAT, SETS, VERSION, batch, fingerprint, fit, transform
from .integrity import POLICY, audit, key
from .stats import Report, distributions
from .view import folds, load

FILES = ("report.json", "report.md", "folds.json", "features.json", "fit-demo.json")


def identity(root: Path, dataset: str, version: str) -> tuple[Path, dict[str, object]]:
    _, m = read_manifest(root, dataset, version)
    split = {name: m.artifact_checksums[name] for name in ("development.jsonl", "holdout.jsonl")}
    ref: dict[str, object] = {
        "dataset": dataset,
        "dataset_version": version,
        "raw_sha256": m.sha256,
        "records_sha256": m.processed_sha256,
        "split": split,
        "policy": POLICY,
        "schema": VERSION,
        "code": "analysis-v1",
        "seed": SEED,
        "python": platform.python_version(),
        "specs": {fs: fingerprint(fs) for fs in SETS},
    }
    return root / "analysis" / dataset / version / digest(encoded(ref))[:24], ref


def read_report(root: Path, dataset: str, version: str) -> Report:
    folder, ref = identity(root, dataset, version)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    path = folder / "report.json"
    if (
        manifest.get("reference") != ref
        or path.stat().st_size > 100000
        or file_sha(path) != manifest["checksums"]["report.json"]
    ):
        raise ValueError("invalid_analysis_report")
    report = Report.model_validate_json(path.read_bytes())
    if (report.dataset, report.version, report.view_version) != (dataset, version, folder.name):
        raise ValueError("analysis_identity")
    return report


def verify_artifacts(root: Path, dataset: str, version: str) -> Report:
    report = read_report(root, dataset, version)
    folder, _ = identity(root, dataset, version)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    for name in FILES:
        if file_sha(folder / name) != manifest["checksums"][name]:
            raise ValueError("analysis_corruption")
    return report


def run(root: Path, dataset: str, version: str) -> Report:
    counts, excluded = audit(root, dataset, version)
    view = load(root, dataset, version, excluded)
    membership = folds(view, 5)
    before = load(root, dataset, version, set())
    folder, ref = identity(root, dataset, version)
    counts_by_fold = [
        [sum(f == i and y == j for f, y in zip(membership, view.y, strict=True)) for j in (0, 1)]
        for i in range(5)
    ]
    groups: dict[str, list[int]] = defaultdict(list)
    for x, y in zip(view.x, view.y, strict=True):
        groups[key(x, APPROVED)].append(y)
    data, assoc = distributions(view, membership)
    matrices = {fs: batch(view.x, fs, fingerprint(fs)) for fs in SETS}
    parity = all(
        matrix == [transform(row, fs, fingerprint(fs)) for row in view.x]
        for fs, matrix in matrices.items()
    )
    states = {
        fs: {
            family: fit(view, membership, 0, fs, family, "development-training")
            for family in ("linear", "tree")
        }
        for fs in SETS
    }
    nonfinite = sum(
        not math.isfinite(x)
        for pairs in states.values()
        for s in pairs.values()
        for row in view.x
        for x in s.apply(row)
    )
    if nonfinite or not parity:
        raise ValueError("preprocessing_integrity")
    report = Report(
        dataset=dataset,
        version=version,
        view_version=folder.name,
        policy=POLICY,
        audit=counts,
        eligible=len(view.x),
        positives=sum(view.y),
        before_positive=sum(before.y),
        folds=counts_by_fold,
        distributions=data,
        associations=assoc,
        repeated_groups=sum(len(g) > 1 for g in groups.values()),
        conflicting_groups=sum(len(set(g)) > 1 for g in groups.values()),
        variants=SETS,
        parity=parity,
        nonfinite=nonfinite,
    )
    lines = [
        "# Development analysis",
        "",
        f"Dataset {dataset} ({version}), view {folder.name}.",
        f"Eligible {report.eligible}, churn {report.positives}.",
        f"Validation counts [non-churn, churn]: {report.folds}.",
        "",
        "| Feature | Unit | N | Mean | Median | IQR | Outliers |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for d in data:
        if d.name not in CAT:
            s = d.summary
            lines.append(
                f"| {d.name} | {d.unit} | {d.n} | {s['mean']:.3f} | {s['median']:.3f} | {s['iqr']:.3f} | {s['outliers']:.0f} |"
            )
    with staging(root) as temp:
        staged = temp / "analysis"
        staged.mkdir()
        (staged / "report.json").write_bytes(encoded(report.model_dump()))
        (staged / "report.md").write_bytes(("\n".join(lines) + "\n").encode())
        (staged / "folds.json").write_bytes(
            encoded(
                {
                    "algorithm": "greedy normalized class load",
                    "seed": SEED,
                    "members": list(zip(view.ids, membership, strict=True)),
                }
            )
        )
        diagnostics = {}
        for fs, matrix in matrices.items():
            columns = list(zip(*matrix, strict=True))
            if len({tuple(row) for row in matrix}) != len(groups):
                raise ValueError("transform_collapsed_vectors")
            diagnostics[fs] = {
                "duplicate_columns": sum(v - 1 for v in Counter(columns).values()),
                "constant": [n for n, c in zip(SETS[fs], columns, strict=True) if len(set(c)) == 1],
                "dimensions": [len(matrix), len(columns)],
            }
        (staged / "features.json").write_bytes(
            encoded(
                {
                    "scope": "unfitted-development",
                    "types": "float64",
                    "feature_names": SETS,
                    "values": matrices,
                }
            )
        )
        (staged / "fit-demo.json").write_bytes(
            encoded({fs: {f: asdict(s) for f, s in pairs.items()} for fs, pairs in states.items()})
        )
        sums = {name: file_sha(staged / name) for name in FILES}
        (staged / "manifest.json").write_bytes(
            encoded(
                {
                    "reference": ref,
                    "checksums": sums,
                    "creation": "deterministic CLI publication",
                    "limitations": [
                        "Snapshot only",
                        "Fold demonstration fit is not approved for deployment",
                    ],
                    "outputs": diagnostics,
                }
            )
        )
        publish_dir(staged, folder)
        existing = verify_artifacts(root, dataset, version)
        if json.loads((folder / "manifest.json").read_bytes())["checksums"] != sums:
            raise ValueError("nonreproducible_analysis")
        return existing
