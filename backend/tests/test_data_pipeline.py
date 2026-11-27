"""All row fixtures in this suite are synthetic."""

import csv
import io
import json
import stat
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from retainiq.core.config import Settings
from retainiq.data import acquire as source
from retainiq.data import registry
from retainiq.data.contract import APPROVED, CAPABILITIES, DEMO, NAMES, UCI, Manifest
from retainiq.data.events import Event, OutcomeWindow
from retainiq.data.quality import InvalidData, Quality, normalize, profile
from retainiq.data.split import partitions
from retainiq.main import create_app


def mock_server(monkeypatch, respond):
    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(source.httpx, "Client", lambda **kwargs: client)


@pytest.mark.parametrize("failure", ["redirect", "limit", "timeout"])
def test_network_policy(tmp_path, monkeypatch, failure):
    calls = []

    def respond(req):
        calls.append(req)
        if failure == "timeout":
            raise httpx.ReadTimeout("fixture timeout")
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://elsewhere.invalid/data"})
        return httpx.Response(200, content=b"x" * (source.LIMIT + 1))

    mock_server(monkeypatch, respond)
    with pytest.raises(ValueError):
        source.acquire(tmp_path, UCI)
    assert len(calls) == (3 if failure == "timeout" else 1)
    assert not (tmp_path / "raw").exists() and list((tmp_path / "staging").iterdir()) == []


def test_stream_interruption(monkeypatch, tmp_path):
    def broken():
        yield b"partial"
        raise httpx.ReadError("disconnected")

    mock_server(monkeypatch, lambda req: httpx.Response(200, content=broken()))
    with pytest.raises(ValueError, match="interrupted"):
        source.acquire(tmp_path, UCI)
    assert not registry.versions(tmp_path, UCI)


def test_official_source_pin_and_fixture(tmp_path, monkeypatch):
    b = source.fixture()
    mock_server(monkeypatch, lambda req: httpx.Response(200, content=b))
    with pytest.raises(ValueError, match="checksum"):
        source.acquire(tmp_path, UCI)
    with pytest.raises(ValueError, match="unknown_dataset"):
        source.acquire(tmp_path, "../../other")
    sha = source.acquire(tmp_path, DEMO)
    assert (tmp_path / "raw" / DEMO / sha / "source").read_bytes() == b


@pytest.mark.parametrize(
    "kind", ["traversal", "absolute", "symlink", "duplicates", "expansion", "invalid"]
)
def test_archive_allowlist(kind):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        member = zipfile.ZipInfo(
            {"traversal": "../member", "absolute": "/member"}.get(kind, source.MEMBER)
        )
        if kind == "symlink":
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
        member.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(member, b"x" * 100000 if kind == "expansion" else b"x")
        if kind == "duplicates":
            z.writestr(member, b"x")
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        source.csv_bytes(b"PKbroken" if kind == "invalid" else buf.getvalue())


def mutated(header=None, change=None):
    rows = list(csv.reader(io.StringIO(source.fixture().decode())))
    if header:
        header(rows[0])
    if change:
        rows[1][change[0]] = change[1]
    out = io.StringIO()
    csv.writer(out).writerows(rows)
    return out.getvalue().encode()


@pytest.mark.parametrize(
    ("index", "value", "rule"),
    [
        (13, "", "missing"),
        (13, "2", "category"),
        (9, "0", "category"),
        (0, "abc", "numeric_type"),
        (12, "NaN", "nonfinite"),
        (0, "-1", "domain"),
        (3, "11", "domain"),
    ],
)
def test_invalid_cells(index, value, rule):
    with pytest.raises(InvalidData) as ctx:
        normalize(mutated(change=(index, value)))
    assert [(i.rule, i.column, i.affected_rows, i.severity) for i in ctx.value.issues] == [
        (rule, NAMES[index], 1, "error")
    ]


@pytest.mark.parametrize(
    ("mutate", "rule"),
    [
        (lambda h: h.pop(), "missing_column"),
        (lambda h: h.pop(1), "missing_column"),
        (lambda h: h.append("internal ID"), "identifier"),
        (lambda h: h.append(" CALL failure "), "collision"),
        (lambda h: h.append("unknown"), "unexpected"),
    ],
)
def test_headers(mutate, rule):
    with pytest.raises(InvalidData) as ctx:
        normalize(mutated(header=mutate))
    assert rule in [i.rule for i in ctx.value.issues]


def test_duplicates_and_split():
    rows = normalize(source.fixture())
    rows.extend([dict(rows[0]), dict(rows[0], churn=1 - rows[0]["churn"])])
    q = profile(rows)
    assert (q.exact_duplicate_excess, q.conflicting_groups, q.predictor_duplicate_groups) == (
        1,
        1,
        1,
    )
    assert partitions(rows) == partitions(rows[::-1])
    assert len(APPROVED) == 8 and not set(APPROVED) & {
        "record_id",
        "churn",
        "status",
        "customer_value",
        "age",
        "age_group",
        "charge_amount",
    }
    assert [k for k, v in CAPABILITIES.items() if v] == ["snapshot_classification"]


@pytest.fixture
def registered(tmp_path):
    source.acquire(tmp_path, DEMO)
    return tmp_path, registry.ingest(tmp_path, DEMO)


def test_registry_integrity(registered):
    root, m = registered
    assert registry.ingest(root, DEMO) == m
    assert registry.verify(root, DEMO, m.version) == m
    samples = list(registry.development(root, DEMO, m.version))
    assert len(samples) == m.development
    assert set(samples[0]["features"]) == set(APPROVED)
    folder, _ = registry.read_manifest(root, DEMO, m.version)
    dev = {s["record_id"] for s in samples}
    final = {
        json.loads(line)["record_id"]
        for line in (folder / "holdout.jsonl").read_bytes().splitlines()
    }
    assert dev.isdisjoint(final) and len(dev | final) == m.row_count
    with pytest.raises(FileNotFoundError):
        registry.read_manifest(root, DEMO, "../../private")
    with pytest.raises(ValidationError):
        Manifest.model_validate({**m.model_dump(), "supported_prediction_horizons_days": [90]})
    with pytest.raises(ValidationError):
        Manifest.model_validate({**m.model_dump(), "holdout": 999})
    (folder / "development.jsonl").write_bytes(b"broken")
    with pytest.raises(ValueError, match="artifact_corruption"):
        registry.ingest(root, DEMO)
    with pytest.raises(ValueError):
        list(registry.development(root, DEMO, m.version))


def test_interruption_and_concurrency(monkeypatch, tmp_path):
    key = source.acquire(tmp_path, DEMO)

    def fail(*args):
        raise OSError("interrupted")

    with monkeypatch.context() as patch:
        patch.setattr(registry, "publish_dir", fail)
        with pytest.raises(OSError):
            registry.ingest(tmp_path, DEMO)
    assert not registry.versions(tmp_path, DEMO)
    assert list((tmp_path / "staging").iterdir()) == []
    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(lambda _: registry.ingest(tmp_path, DEMO), range(2)))
    assert results[0] == results[1] and len(registry.versions(tmp_path, DEMO)) == 1
    (tmp_path / "raw" / DEMO / key / "source").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="raw_corruption"):
        registry.verify(tmp_path, DEMO)


def test_demo_metadata_boundary(registered):
    root, m = registered
    with TestClient(create_app(Settings(data_root=root))) as client:
        assert client.get("/api/v1/datasets").json() == []
        assert client.get(f"/api/v1/datasets/{DEMO}").status_code == 404
    with TestClient(create_app(Settings(data_root=root, public_datasets=[DEMO]))) as client:
        catalog = client.get("/api/v1/datasets")
        obj = catalog.json()[0]
        assert obj["provenance"] == "Synthetic fixture" and obj["rows"] == 40
        assert not any(
            term in catalog.text
            for term in [str(root), "record_id", "acquired_at", "artifact_checksums", "receipt"]
        )
        url = f"/api/v1/datasets/{DEMO}/versions"
        assert client.get(url).json() == [m.version]
        assert client.get(f"{url}/{m.version}/quality").json() == obj
        assert client.get(f"{url}/{'0' * 24}/quality").status_code == 404
        assert client.get("/api/v1/datasets/garbage").status_code == 422
        assert client.post(url).status_code == 405


def test_temporal_contract():
    start = datetime.now(UTC)
    end = start + timedelta(days=1)
    event = Event(customer_id="synthetic", entity="usage", occurred_at=start, available_at=end)
    assert not event.observable(start) and event.observable(end)
    assert OutcomeWindow(cutoff=start, end=end, observed_until=start).censored
    with pytest.raises(ValidationError):
        Event(customer_id="synthetic", entity="intervention", occurred_at=end, available_at=start)


def test_exported_schemas_match():
    location = Path(__file__).resolve().parents[2] / "data"
    for filename, model in [("manifest", Manifest), ("quality", Quality)]:
        assert (
            json.loads((location / (filename + ".schema.json")).read_text())
            == model.model_json_schema()
        )
