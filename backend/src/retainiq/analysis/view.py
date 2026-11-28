from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from retainiq.data.contract import APPROVED, SEED, digest, encoded
from retainiq.data.registry import development

from .integrity import key


@dataclass(frozen=True)
class View:
    ids: list[int]
    x: list[dict[str, int]]
    y: list[int]


def load(root: Path, dataset: str, version: str, quarantine: set[int]) -> View:
    ids = []
    x = []
    y = []
    for sample in development(root, dataset, version):
        rid = cast(int, sample["record_id"])
        if rid in quarantine:
            continue
        row = cast(dict[str, int], sample["features"])
        if set(row) != set(APPROVED) or any(type(v) is not int or v < 0 for v in row.values()):
            raise ValueError("input_schema")
        if row["complains"] not in (0, 1) or row["tariff_plan"] not in (1, 2):
            raise ValueError("invalid_category")
        if type(sample["target"]) is not int or sample["target"] not in (0, 1):
            raise ValueError("input_schema")
        ids.append(rid)
        x.append(row)
        y.append(sample["target"])
    if not set(quarantine).isdisjoint(ids) or len(set(ids)) != len(ids):
        raise ValueError("invalid_development_identity")
    return View(ids, x, y)


def folds(view: View, k: int = 5) -> list[int]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(view.x):
        groups[key(row, APPROVED)].append(i)
    if not 2 <= k <= len(groups):
        raise ValueError("invalid_fold_count")
    totals = [view.y.count(j) / k for j in (0, 1)]
    if min(totals) < 1:
        raise ValueError("insufficient_classes")
    bins = [[0, 0] for _ in range(k)]
    out = [-1] * len(view.x)
    for group in sorted(groups, key=lambda s: (-len(groups[s]), digest(encoded([SEED, s])))):
        indices = groups[group]
        pos = sum(view.y[i] for i in indices)
        size = [len(indices) - pos, pos]

        def increase(f: int, size: list[int] = size) -> float:
            return sum(
                ((bins[f][j] + size[j]) ** 2 - bins[f][j] ** 2) / totals[j] ** 2 for j in (0, 1)
            )

        f = min(range(k), key=increase)
        for j in (0, 1):
            bins[f][j] += size[j]
        for i in indices:
            out[i] = f
    if any(min(pair) == 0 for pair in bins):
        raise ValueError("insufficient_fold_support")
    return out
