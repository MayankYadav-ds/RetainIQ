"""Independently compare the pinned archive to every normalized row and both split files.

Run from the repository root with an explicit store and version directory name.
Only aggregate evidence is printed. This script uses no RetainIQ parsing or grouping code.
"""

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


def reconcile(root: Path, version: str) -> dict[str, object]:
    archive_hash = "696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66"
    if len(version) != 24 or any(c not in "0123456789abcdef" for c in version):
        raise ValueError("Expected a known version identifier")
    folder = root / "processed" / "uci_iranian_churn" / version
    blob = (root / "raw" / "uci_iranian_churn" / archive_hash / "source").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == archive_hash
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        data = z.read("Customer Churn.csv")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    normalized = [
        {"_".join(k.split()).lower(): Decimal(v) for k, v in record.items()}
        for record in rows
    ]
    records = (folder / "records.jsonl").read_bytes()
    for i, (row, line) in enumerate(
        zip(normalized, records.splitlines(), strict=True), 1
    ):
        obj = json.loads(line, parse_float=Decimal)
        assert obj.pop("record_id") == i and obj == row
    seen = set()
    groups: dict[tuple[Decimal, ...], str] = {}
    counts = {}
    for role in ("development", "holdout"):
        n = 0
        for line in (folder / (role + ".jsonl")).read_bytes().splitlines():
            obj = json.loads(line, parse_float=Decimal)
            i = obj["record_id"]
            assert 1 <= i <= len(rows) and i not in seen
            seen.add(i)
            n += 1
            row = normalized[i - 1]
            assert obj["target"] == row["churn"]
            assert set(obj["features"]) == {
                "call_failure",
                "complains",
                "subscription_length",
                "seconds_of_use",
                "frequency_of_use",
                "frequency_of_sms",
                "distinct_called_numbers",
                "tariff_plan",
            }
            assert all(value == row[k] for k, value in obj["features"].items())
            key = tuple(v for k, v in row.items() if k != "churn")
            assert groups.setdefault(key, role) == role
        counts[role] = n
    assert len(seen) == len(rows)
    vectors = defaultdict(list)
    exact = Counter(tuple(r.values()) for r in normalized)
    for r in normalized:
        vectors[tuple(v for k, v in r.items() if k != "churn")].append(int(r["churn"]))
    report = json.loads((folder / "quality.json").read_bytes())
    checks = {
        "rows": len(rows),
        "columns": len(rows[0]),
        "missing": sum(v == "" for r in rows for v in r.values()),
        "target_counts": dict(Counter(r["Churn"] for r in rows)),
        "exact_duplicate_groups": sum(n > 1 for n in exact.values()),
        "exact_duplicate_excess": len(rows) - len(exact),
        "predictor_duplicate_groups": sum(len(g) > 1 for g in vectors.values()),
        "conflicting_groups": sum(len(set(g)) > 1 for g in vectors.values()),
    }
    assert all(report[k] == v for k, v in checks.items())
    return {
        **checks,
        **counts,
        "raw_bytes": len(blob),
        "csv_bytes": len(data),
        "processed_sha256": hashlib.sha256(records).hexdigest(),
        "csv_sha256": hashlib.sha256(data).hexdigest(),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("data"))
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    print(json.dumps(reconcile(a.root, a.version), indent=2))
