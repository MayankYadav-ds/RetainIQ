import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from .acquire import LIMIT, csv_bytes, fixture, publish_dir, staging
from .contract import (
    APPROVED,
    CITATION,
    CSV_SHA,
    FILES,
    UCI,
    URL,
    ZIP_SHA,
    Manifest,
    checked_id,
    digest,
    encoded,
    file_sha,
    schema_columns,
    version_for,
)
from .quality import Quality, Row, group_key, markdown, normalize, profile
from .split import partitions


def default_root() -> Path:
    # The data CLI and editable-install API share this location regardless of cwd.
    return Path(
        os.environ.get(
            "RETAINIQ_DATA_ROOT",
            str(
                Path(__file__).resolve().parents[4] / "data"
                if (Path(__file__).resolve().parents[4] / "data/manifest.schema.json").exists()
                else Path.cwd() / ".retainiq-data"
            ),
        )
    )


def known_raw(dataset: str) -> tuple[str, ...]:
    checked_id(dataset)
    return (ZIP_SHA, CSV_SHA) if dataset == UCI else (digest(fixture()),)


def raw_object(root: Path, dataset: str, sha: str | None = None) -> tuple[str, Path]:
    for key in known_raw(dataset):
        if sha is not None and sha != key:
            continue
        folder = root / "raw" / dataset / key
        if not folder.exists():
            continue
        src = folder / "source"
        if src.stat().st_size > LIMIT or file_sha(src) != key:
            raise ValueError("raw_corruption")
        return key, folder
    raise FileNotFoundError("source_missing")


def versions(root: Path, dataset: str) -> list[str]:
    return [
        v
        for sha in known_raw(dataset)
        if (
            root / "processed" / dataset / (v := version_for(dataset, sha)) / "manifest.json"
        ).is_file()
    ]


def read_manifest(root: Path, dataset: str, version: str | None = None) -> tuple[Path, Manifest]:
    keys = versions(root, dataset)
    if not keys or (version is not None and version not in keys):
        raise FileNotFoundError("version_missing")
    folder = root / "processed" / dataset / (version or keys[0])
    m = Manifest.model_validate_json((folder / "manifest.json").read_bytes())
    if m.dataset_name != dataset or m.version != folder.name:
        raise ValueError("identity_mismatch")
    return folder, m


def materialize(folder: Path, rows: list[Row], quality: Quality) -> int:
    chosen = partitions(rows)
    dev_count = 0
    with (
        (folder / "records.jsonl").open("wb") as full,
        (folder / "development.jsonl").open("wb") as dev,
        (folder / "holdout.jsonl").open("wb") as final,
    ):
        for idx, row in enumerate(rows):
            entry = {"record_id": idx + 1, **row}
            full.write(encoded(entry))
            sample = encoded(
                {
                    "record_id": idx + 1,
                    "features": {n: row[n] for n in APPROVED},
                    "target": int(row["churn"]),
                }
            )
            if group_key(row) in chosen:
                final.write(sample)
            else:
                dev.write(sample)
                dev_count += 1
    (folder / "quality.json").write_bytes(encoded(quality.model_dump()))
    (folder / "quality.md").write_bytes(markdown(quality).encode())
    return dev_count


def verify(root: Path, dataset: str, version: str | None = None) -> Manifest:
    folder, m = read_manifest(root, dataset, version)
    _, raw = raw_object(root, dataset, m.sha256)
    receipt = json.loads((raw / "receipt.json").read_bytes())
    if (
        receipt["sha256"] != m.sha256
        or receipt["acquired_at"] != m.acquired_at.isoformat()
        or m.source_bytes != (raw / "source").stat().st_size
    ):
        raise ValueError("receipt_mismatch")
    for name in FILES:
        if file_sha(folder / name) != m.artifact_checksums[name]:
            raise ValueError("artifact_corruption")
    q = Quality.model_validate_json((folder / "quality.json").read_bytes())
    if q.rows != m.row_count or sum(q.target_counts.values()) != q.rows:
        raise ValueError("report_mismatch")
    return m


def ingest(
    root: Path,
    dataset: Literal["uci_iranian_churn", "synthetic_churn_fixture"],
    sha: str | None = None,
) -> Manifest:
    key, raw = raw_object(root, dataset, sha)
    data = (raw / "source").read_bytes()
    rows = normalize(csv_bytes(data))
    q = profile(rows)
    version = version_for(dataset, key)
    with staging(root) as temp:
        folder = temp / "version"
        folder.mkdir()
        dev = materialize(folder, rows, q)
        hashes = {n: file_sha(folder / n) for n in FILES}
        receipt = json.loads((raw / "receipt.json").read_bytes())
        m = Manifest(
            dataset_name=dataset,
            source=URL if dataset == UCI else "fixture:synthetic-v1",
            license="CC BY 4.0" if dataset == UCI else "MIT",
            attribution=CITATION if dataset == UCI else "RetainIQ deterministic synthetic fixture",
            provenance="official UCI benchmark" if dataset == UCI else "synthetic demonstration",
            known_limitations=[
                "No customer identifiers, dated events, treatment assignments or verified revenue."
            ],
            version=version,
            sha256=key,
            acquired_at=receipt["acquired_at"],
            source_file_name=(
                "iranian+churn+dataset.zip" if key == ZIP_SHA else "Customer Churn.csv"
            )
            if dataset == UCI
            else "synthetic.csv",
            source_bytes=len(data),
            schema=schema_columns(),
            row_count=len(rows),
            development=dev,
            holdout=len(rows) - dev,
            artifact_checksums=hashes,
            processed_sha256=hashes["records.jsonl"],
            validation_status="passed_with_warnings" if q.issues else "passed",
        )
        if receipt["sha256"] != key:
            raise ValueError("receipt_mismatch")
        # Read back complete rows, separated feature/label contracts and partition integrity.
        seen = set()
        grouped: dict[bytes, str] = {}
        for part, expected in [("development", dev), ("holdout", len(rows) - dev)]:
            count = 0
            with (folder / (part + ".jsonl")).open("rb") as stream:
                for line in stream:
                    obj = json.loads(line)
                    rid = obj["record_id"]
                    row = rows[rid - 1]
                    if (
                        rid in seen
                        or obj["features"] != {n: row[n] for n in APPROVED}
                        or obj["target"] != row["churn"]
                        or grouped.setdefault(group_key(row), part) != part
                    ):
                        raise ValueError("partition_integrity")
                    seen.add(rid)
                    count += 1
            if expected != count:
                raise ValueError("partition_size")
        with (folder / "records.jsonl").open("rb") as stream:
            for idx, (line, row) in enumerate(zip(stream, rows, strict=True), 1):
                if json.loads(line) != {"record_id": idx, **row}:
                    raise ValueError("readback_mismatch")
        if len(seen) != len(rows):
            raise ValueError("unassigned_rows")
        (folder / "manifest.json").write_bytes(encoded(m.model_dump(mode="json", by_alias=True)))
        publish_dir(folder, root / "processed" / dataset / version)
        existing = verify(root, dataset, version)
        if existing != m:
            raise ValueError("conflicting_version")
        return existing


def development(root: Path, dataset: str, version: str) -> Iterator[dict[str, object]]:
    verify(root, dataset, version)
    folder, _ = read_manifest(root, dataset, version)
    with (folder / "development.jsonl").open("rb") as f:
        for line in f:
            sample: dict[str, object] = json.loads(line)
            yield sample
