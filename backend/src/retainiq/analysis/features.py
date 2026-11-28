"""Shared versioned raw-to-feature contract and fold-specific preprocessing."""

import math
import statistics
from dataclasses import dataclass
from typing import Literal

from retainiq.data.contract import APPROVED, digest, encoded

from .integrity import key
from .view import View

VERSION = "features-v1"
CAT = ("complains", "tariff_plan")
CATALOG = {
    "has_call_failure": (
        "call_failure",
        "int(call_failure > 0)",
        "Separate any failure from failure count",
    ),
    "complaint_with_failure": (
        "complains, call_failure",
        "complains * int(call_failure > 0)",
        "Describe co-occurring service signals",
    ),
    "log_seconds_of_use": (
        "seconds_of_use",
        "log1p(seconds_of_use)",
        "Compress the upper tail of total call seconds",
    ),
    "log_frequency_of_sms": (
        "frequency_of_sms",
        "log1p(frequency_of_sms)",
        "Compress the upper tail of SMS counts",
    ),
}
SETS = {
    "FS01": APPROVED,
    "FS02": [*APPROVED, *list(CATALOG)[:2]],
    "FS03": [*APPROVED, *list(CATALOG)[2:]],
}


def fingerprint(fs: str) -> str:
    return digest(encoded([VERSION, fs, SETS[fs], CATALOG]))


def transform(row: dict[str, int], fs: str, schema: str) -> list[float]:
    if fs not in SETS or schema != fingerprint(fs) or set(row) != set(APPROVED):
        raise ValueError("feature_contract_mismatch")
    if any(type(v) is not int or not 0 <= v <= 2**53 - 1 for v in row.values()):
        raise ValueError("invalid_feature_domain")
    if row["complains"] not in (0, 1):
        raise ValueError("invalid_complaint")
    values: dict[str, float] = dict(row)
    values.update(
        has_call_failure=int(row["call_failure"] > 0),
        complaint_with_failure=int(row["call_failure"] > 0) * row["complains"],
        log_seconds_of_use=math.log1p(row["seconds_of_use"]),
        log_frequency_of_sms=math.log1p(row["frequency_of_sms"]),
    )
    return [float(values[n]) for n in SETS[fs]]


def batch(rows: list[dict[str, int]], fs: str, schema: str) -> list[list[float]]:
    return [transform(r, fs, schema) for r in rows]


@dataclass(frozen=True)
class FoldState:
    schema: str
    fs: str
    fold: int
    family: str
    names: list[str]
    means: list[float]
    scales: list[float]
    scope: Literal["development-training-only"] = "development-training-only"

    def apply(self, row: dict[str, int]) -> list[float]:
        v = design(row, self.fs, self.schema)
        return [(x - m) / s for x, m, s in zip(v, self.means, self.scales, strict=True)]


def design(row: dict[str, int], fs: str, schema: str) -> list[float]:
    vals = transform(row, fs, schema)
    idx = SETS[fs].index("tariff_plan")
    plan = vals.pop(idx)
    return [*vals, float(plan == 2), float(plan not in (1, 2))]


def fit(view: View, membership: list[int], fold: int, fs: str, family: str, role: str) -> FoldState:
    if (
        role != "development-training"
        or family not in ("linear", "tree")
        or len(membership) != len(view.x)
        or fold not in membership
    ):
        raise ValueError("invalid_fit_scope")
    membership_by_group: dict[str, int] = {}
    for row, i in zip(view.x, membership, strict=True):
        if i < 0 or membership_by_group.setdefault(key(row, APPROVED), i) != i:
            raise ValueError("invalid_fold_groups")
    rows = [x for x, f in zip(view.x, membership, strict=True) if f != fold]
    return fit_subset(rows, fs, family, fold)


def fit_subset(rows: list[dict[str, int]], fs: str, family: str, fold: int) -> FoldState:
    """Fit on a caller-provided and already isolated development training subset."""
    if family not in ("linear", "tree"):
        raise ValueError("invalid_fit_family")
    schema = fingerprint(fs)
    train = [design(x, fs, schema) for x in rows]
    if not train:
        raise ValueError("empty_training_fold")
    names = [n for n in SETS[fs] if n != "tariff_plan"] + ["tariff_contract", "tariff_unknown"]
    means = []
    scales = []
    for n, col in zip(names, zip(*train, strict=True), strict=True):
        scale = family == "linear" and n not in (
            "complains",
            "tariff_contract",
            "tariff_unknown",
            "has_call_failure",
            "complaint_with_failure",
        )
        means.append(statistics.mean(col) if scale else 0.0)
        scales.append((statistics.pstdev(col) or 1.0) if scale else 1.0)
    return FoldState(schema, fs, fold, family, names, means, scales)
