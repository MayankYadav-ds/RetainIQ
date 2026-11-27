import csv
import io
import math
import statistics as stats
from collections import Counter, defaultdict
from typing import Any, Literal

from .contract import CATEGORIES, NAMES, Contract, encoded

Row = dict[str, int | float]


class Issue(Contract):
    rule: str
    severity: Literal["error", "warning"]
    column: str
    affected_rows: int
    evidence: str
    handling: str


class InvalidData(ValueError):
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        super().__init__("schema_validation_failed")


def issue(rule: str, col: str, n: int, note: str, action: str, hard: bool = False) -> Issue:
    return Issue(
        rule=rule,
        column=col,
        affected_rows=n,
        evidence=note,
        handling=action,
        severity="error" if hard else "warning",
    )


class Quality(Contract):
    schema_version: Literal[1] = 1
    rows: int
    columns: int
    features: int
    targets: int
    types: dict[str, int]
    target_counts: dict[str, int]
    prevalence: float
    exact_duplicate_groups: int
    exact_duplicate_excess: int
    predictor_duplicate_groups: int
    conflicting_groups: int
    missing: int
    fields: dict[str, dict[str, Any]]
    issues: list[Issue]


def normalize(blob: bytes) -> list[Row]:
    reader = csv.reader(io.StringIO(blob.decode("utf-8-sig"), newline=""), strict=True)
    names = ["_".join(c.lower().split()) for c in next(reader, [])]
    if len(names) != len(set(names)) or set(names) != set(NAMES):
        errors = []
        for name in sorted(set(names) | set(NAMES)):
            if name not in NAMES or names.count(name) != 1:
                rule = (
                    ("identifier" if "id" in name else "unexpected")
                    if name not in NAMES
                    else ("missing_column" if name not in names else "collision")
                )
                errors.append(
                    issue(
                        rule,
                        name if name in NAMES else "unrecognized",
                        0,
                        "Header discrepancy",
                        "Review source contract",
                        True,
                    )
                )
        raise InvalidData(errors)
    rows: list[Row] = []
    counts: Counter[tuple[str, str]] = Counter()
    for i, values in enumerate(reader):
        if i >= 10000:
            raise ValueError("row_limit")
        if len(values) != len(names):
            counts["field_count", "schema"] += 1
            continue
        row: Row = {}
        for col, cell in zip(names, values, strict=True):
            code = ""
            try:
                if not cell.strip():
                    code = "missing"
                elif not math.isfinite(float(cell)):
                    code = "nonfinite"
                else:
                    value = float(cell) if col == "customer_value" else int(cell)
                    if value < 0 or (col == "charge_amount" and value > 10):
                        code = "domain"
                    elif col in CATEGORIES and value not in CATEGORIES[col]:
                        code = "category"
                    else:
                        row[col] = value
            except (ValueError, OverflowError):
                code = "numeric_type"
            if code:
                counts[code, col] += 1
        if len(row) == len(names):
            rows.append({n: row[n] for n in NAMES})
    if counts:
        raise InvalidData(
            [
                issue(rule, col, n, "Invalid input cells", "Reject batch and inspect source", True)
                for (rule, col), n in sorted(counts.items())
            ]
        )
    if len(rows) < 2:
        raise ValueError("insufficient_rows")
    return rows


def group_key(row: Row) -> bytes:
    return encoded([row[n] for n in NAMES[:-1]])


def profile(rows: list[Row]) -> Quality:
    issues = []
    fields = {}
    for n in NAMES:
        vals = [r[n] for r in rows]
        freq = Counter(vals)
        q1, med, q3 = stats.quantiles(vals, method="inclusive")
        f: dict[str, Any] = {
            "missing": 0,
            "missing_percent": 0,
            "distinct": len(freq),
            "min": min(vals),
            "max": max(vals),
            "q1": q1,
            "median": med,
            "q3": q3,
            "mean": stats.mean(vals),
            "sample_sd": stats.stdev(vals),
        }
        if n in CATEGORIES or n == "charge_amount":
            f["frequencies"] = {str(v): k for v, k in sorted(freq.items())}
        fields[n] = f
        common = max(freq.values())
        if common >= 0.95 * len(vals):
            issues.append(
                issue(
                    "constant" if len(freq) == 1 else "near_constant",
                    n,
                    common,
                    "Modal share >=95%",
                    "Review on development data",
                )
            )
        width = q3 - q1
        extreme = (
            sum(x < q1 - 3 * width or x > q3 + 3 * width for x in vals)
            if width and n not in CATEGORIES
            else 0
        )
        if extreme:
            issues.append(
                issue("extreme", n, extreme, "Outside outer Tukey fences", "Retain and review")
            )
    bands = sum(r["charge_amount"] == 10 for r in rows)
    if bands:
        issues.append(
            issue(
                "documented_range",
                "charge_amount",
                bands,
                "Observed band 10 exceeds documented 9",
                "Preserve; withhold from default features",
            )
        )
    exact = Counter(encoded(r) for r in rows)
    groups: dict[bytes, list[int]] = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(int(row["churn"]))
    dup = [g for g in groups.values() if len(g) > 1]
    conflicts = [g for g in dup if len(set(g)) > 1]
    for rule, count in [
        ("exact_duplicates", sum(v for v in exact.values() if v > 1)),
        ("predictor_duplicates", sum(map(len, dup))),
        ("conflicting_labels", sum(map(len, conflicts))),
    ]:
        if count:
            issues.append(
                issue(
                    rule,
                    "all",
                    count,
                    "Matching canonical vectors",
                    "Retain all observations and group partitions",
                )
            )
    counts = {str(i): sum(r["churn"] == i for r in rows) for i in (0, 1)}
    return Quality(
        rows=len(rows),
        columns=14,
        features=13,
        targets=1,
        types={"integer": 13, "number": 1},
        target_counts=counts,
        prevalence=counts["1"] / len(rows),
        exact_duplicate_groups=sum(v > 1 for v in exact.values()),
        exact_duplicate_excess=sum(v - 1 for v in exact.values()),
        predictor_duplicate_groups=len(dup),
        conflicting_groups=len(conflicts),
        missing=0,
        fields=fields,
        issues=issues,
    )


def markdown(q: Quality) -> str:
    lines = [
        "# Aggregate quality report",
        "",
        f"{q.rows} observations, {q.features} predictors, one target. Missing cells: {q.missing}.",
        f"Target counts {q.target_counts}. Prevalence {q.prevalence:.4%}.",
        (
            f"Exact duplicate excess {q.exact_duplicate_excess}. "
            f"Repeated predictor groups {q.predictor_duplicate_groups}; "
            f"conflicting groups {q.conflicting_groups}."
        ),
        "",
        (
            "| Field | Missing (%) | Distinct | Min | Q1 | Median | Q3 | "
            "Max | Mean | Sample SD | Frequencies |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for col, f in q.fields.items():
        lines.append(
            f"| {col} | 0 | "
            + " | ".join(
                f"{f[k]:.5g}"
                for k in ("distinct", "min", "q1", "median", "q3", "max", "mean", "sample_sd")
            )
            + f" | {f.get('frequencies', '')} |"
        )
    lines.extend(
        ["", "## Warnings", ""]
        + [
            f"- {i.rule}, {i.column}: {i.affected_rows} rows. {i.evidence}. {i.handling}."
            for i in q.issues
        ]
    )
    return "\n".join(lines) + "\n"
