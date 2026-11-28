"""Development-only inputs and immutable outer validation membership."""

import json
from dataclasses import dataclass
from pathlib import Path

from retainiq.analysis.integrity import audit, key
from retainiq.analysis.registry import identity, verify_artifacts
from retainiq.analysis.view import View, load
from retainiq.data.contract import APPROVED, UCI, digest, encoded, file_sha
from retainiq.data.registry import read_manifest

from .protocol import DATASET, FOLDS, HOLDOUT, RECORDS, VIEW


@dataclass(frozen=True)
class Cohort:
    data: View
    outer: list[int]
    reference: dict[str, str]


def subset(v: View, ix: list[int]) -> View:
    return View([v.ids[i] for i in ix], [v.x[i] for i in ix], [v.y[i] for i in ix])


def cohort(root: Path, dataset: str, version: str, view_version: str) -> Cohort:
    report = verify_artifacts(root, dataset, version)
    folder, _ = identity(root, dataset, version)
    if report.view_version != view_version:
        raise ValueError("view_mismatch")
    _, excluded = audit(root, dataset, version)
    v = load(root, dataset, version, excluded)
    _, m = read_manifest(root, dataset, version)
    path = folder / "folds.json"
    sha = file_sha(path)
    ref = {
        "dataset": dataset,
        "version": version,
        "view": view_version,
        "folds": sha,
        "holdout": m.artifact_checksums["holdout.jsonl"],
        "records": m.processed_sha256,
        "development": digest(encoded(v.ids)),
    }
    if dataset == UCI and (
        (version, view_version, sha, ref["holdout"], m.processed_sha256)
        != (DATASET, VIEW, FOLDS, HOLDOUT, RECORDS)
        or len(v.x) != 2480
        or sum(v.y) != 372
    ):
        raise ValueError("frozen_uci_identity")
    members = json.loads(path.read_bytes())["members"]
    if [r for r, _ in members] != v.ids:
        raise ValueError("membership_mismatch")
    outer = [int(f) for _, f in members]
    groups: dict[str, int] = {}
    for x, i in zip(v.x, outer, strict=True):
        k = key(x, APPROVED)
        if not 0 <= i < 5 or groups.setdefault(k, i) != i:
            raise ValueError("outer_group_mismatch")
    if any({y for y, f in zip(v.y, outer, strict=True) if f == i} != {0, 1} for i in range(5)):
        raise ValueError("outer_class_support")
    return Cohort(v, outer, ref)
