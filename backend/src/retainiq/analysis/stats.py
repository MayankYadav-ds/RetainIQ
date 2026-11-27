"""Descriptive development statistics. No tests of statistical significance."""

import math
import statistics as st
from collections import Counter
from itertools import combinations

from pydantic import BaseModel

from retainiq.data.contract import APPROVED

from .features import CAT
from .view import View


class Cell(BaseModel):
    label: str
    count: int
    churn: int | None = None
    low: float | None = None
    high: float | None = None


class Distribution(BaseModel):
    name: str
    unit: str
    n: int
    missing: int
    summary: dict[str, float]
    cells: list[Cell]
    class_means: list[float]
    effect: float | None
    interval: list[float]
    fold_means: list[float]


class Association(BaseModel):
    left: str
    right: str
    r: float


class Report(BaseModel):
    dataset: str
    version: str
    view_version: str
    policy: str
    audit: dict[str, int]
    eligible: int
    positives: int
    before_positive: int
    folds: list[list[int]]
    distributions: list[Distribution]
    associations: list[Association]
    repeated_groups: int
    conflicting_groups: int
    variants: dict[str, list[str]]
    parity: bool
    nonfinite: int


UNITS = dict(
    zip(
        APPROVED,
        [
            "failures",
            "indicator",
            "months",
            "seconds",
            "calls",
            "messages",
            "destinations",
            "plan code",
        ],
        strict=True,
    )
)


def percentile(v: list[int], q: float) -> float:
    p = (len(v) - 1) * q
    i = int(p)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (p - i)


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, center - half), min(1.0, center + half)


def distributions(view: View, fold: list[int]) -> tuple[list[Distribution], list[Association]]:
    columns = {n: [x[n] for x in view.x] for n in APPROVED}
    result = []
    for n, values in columns.items():
        ordered = sorted(values)
        total = len(values)
        freq = Counter(values)
        summary = {
            "distinct": float(len(freq)),
            "zero": float(freq[0]),
            "modal_share": max(freq.values()) / total,
        }
        cells = []
        means = []
        effect = None
        interval = []
        stability = []
        if n in CAT:
            # Suppress all conditionals if any class-by-category cell is too small.
            counts = {
                v: sum(y for y, x in zip(view.y, values, strict=True) if x == v) for v in freq
            }
            safe = all(min(counts[v], freq[v] - counts[v]) >= 10 for v in freq)
            for v, k in sorted(freq.items()):
                lo, hi = wilson(counts[v], k)
                cells.append(
                    Cell(
                        label=str(v),
                        count=k,
                        churn=counts[v] if safe else None,
                        low=lo if safe else None,
                        high=hi if safe else None,
                    )
                )
        else:
            mean = st.mean(values)
            sd = st.pstdev(values)
            q1, q3 = [percentile(ordered, q) for q in (0.25, 0.75)]
            summary.update(
                min=ordered[0],
                max=ordered[-1],
                mean=mean,
                median=st.median(values),
                sd=st.stdev(values),
                iqr=q3 - q1,
                p05=percentile(ordered, 0.05),
                p95=percentile(ordered, 0.95),
                skew=st.mean(((v - mean) / sd) ** 3 for v in values) if sd else 0.0,
                outliers=sum(v < q1 - 1.5 * (q3 - q1) or v > q3 + 1.5 * (q3 - q1) for v in values),
            )
            width = max(1, math.ceil((ordered[-1] - ordered[0] + 1) / 8))
            for low in range(ordered[0], ordered[-1] + 1, width):
                cells.append(
                    Cell(
                        label=f"{low}–{min(low + width - 1, ordered[-1])}",
                        count=sum(low <= v < low + width for v in values),
                    )
                )
            sets = [[x for x, y in zip(values, view.y, strict=True) if y == j] for j in [0, 1]]
            if min(map(len, sets)) >= 10:
                means = [st.mean(g) for g in sets]
                variances = [st.variance(g) for g in sets]
                pooled = math.sqrt(sum(variances) / 2)
                delta = means[1] - means[0]
                effect = delta / pooled if pooled else None
                se = math.sqrt(sum(v / len(g) for v, g in zip(variances, sets, strict=True)))
                interval = [delta - 1.96 * se, delta + 1.96 * se]
            stability = [
                st.mean(v for v, f in zip(values, fold, strict=True) if f == i)
                for i in sorted(set(fold))
            ]
        result.append(
            Distribution(
                name=n,
                unit=UNITS[n],
                n=total,
                missing=0,
                summary=summary,
                cells=cells,
                class_means=means,
                effect=effect,
                interval=interval,
                fold_means=stability,
            )
        )
    associations = [
        Association(left=a, right=b, r=st.correlation(columns[a], columns[b]))
        for a, b in combinations(columns, 2)
        if a not in CAT and b not in CAT and len(set(columns[a])) > 1 and len(set(columns[b])) > 1
    ]
    return result, associations
