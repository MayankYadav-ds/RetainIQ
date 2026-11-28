import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from retainiq.analysis.features import batch, fingerprint, fit, transform
from retainiq.analysis.integrity import audit
from retainiq.analysis.registry import identity, run, verify_artifacts
from retainiq.analysis.stats import percentile, wilson
from retainiq.analysis.view import View, folds, load
from retainiq.core.config import Settings
from retainiq.data.acquire import acquire
from retainiq.data.contract import APPROVED, DEMO, encoded, file_sha
from retainiq.data.registry import ingest, read_manifest
from retainiq.main import create_app


@pytest.fixture
def registered(tmp_path: Path):
    acquire(tmp_path, DEMO)
    return tmp_path, ingest(tmp_path, DEMO).version


def test_projected_overlap_and_label_blindness(registered, monkeypatch):
    root, version = registered
    folder, m = read_manifest(root, DEMO, version)
    dev = json.loads((folder / "development.jsonl").read_bytes().splitlines()[0])["record_id"]
    final = json.loads((folder / "holdout.jsonl").read_bytes().splitlines()[0])["record_id"]
    path = folder / "records.jsonl"
    rows = [json.loads(s) for s in path.read_bytes().splitlines()]
    rows[final - 1].update({n: rows[dev - 1][n] for n in APPROVED}, status=2, churn="forbidden")
    path.write_bytes(b"".join(encoded(r) for r in rows))
    path = folder / "holdout.jsonl"
    path.write_bytes(path.read_bytes().replace(b'"target":', b'"discarded":'))
    # Altered fixture only: bypass source checks to isolate membership and label use.
    monkeypatch.setattr("retainiq.analysis.integrity.verify", lambda *args: m)
    before = file_sha(path)
    result, excluded = audit(root, DEMO, version)
    assert result["shared_full"] == 0 and result["shared_approved"] == 1 and excluded == {dev}
    assert audit(root, DEMO, version) == (result, excluded)
    assert file_sha(path) == before
    rows[final - 1]["status"] = rows[dev - 1]["status"]
    rows[final - 1]["customer_value"] = rows[dev - 1]["customer_value"]
    (folder / "records.jsonl").write_bytes(b"".join(encoded(r) for r in rows))
    with pytest.raises(ValueError, match="full_vector_overlap"):
        audit(root, DEMO, version)


def test_grouped_folds_and_training_fit(registered):
    root, version = registered
    _, excluded = audit(root, DEMO, version)
    original = load(root, DEMO, version, excluded)
    view = View(
        [*original.ids, 999], [*original.x, original.x[0]], [*original.y, 1 - original.y[0]]
    )
    member = folds(view)
    assert member == folds(view) and member[0] == member[-1]
    assert all(
        {y for f, y in zip(member, view.y, strict=True) if f == i} == {0, 1} for i in range(5)
    )
    with pytest.raises(ValueError):
        folds(view, 1)
    with pytest.raises(ValueError):
        fit(view, member, 0, "FS01", "linear", "holdout")
    state = fit(view, member, 0, "FS01", "linear", "development-training")
    expected = sum(x["call_failure"] for f, x in zip(member, view.x, strict=True) if f != 0) / sum(
        f != 0 for f in member
    )
    assert state.means[0] == pytest.approx(expected)
    row = {**view.x[0], "tariff_plan": 99}
    assert state.apply(row)[-1] == 1
    assert batch([row], "FS02", fingerprint("FS02")) == [
        transform(row, "FS02", fingerprint("FS02"))
    ]
    for invalid in [
        {**row, "record_id": 1},
        {**row, "churn": 0},
        {**row, "seconds_of_use": -1},
        {**row, "seconds_of_use": None},
    ]:
        with pytest.raises(ValueError):
            transform(invalid, "FS02", fingerprint("FS02"))
    with pytest.raises(ValueError):
        transform(row, "FS02", "stale_schema")


def test_known_statistics():
    assert percentile([0, 10, 20], 0.25) == 5
    lo, hi = wilson(5, 10)
    assert (lo, hi) == pytest.approx((0.236593, 0.763407), abs=1e-6)


def test_report_publication_and_privacy(registered):
    root, version = registered
    report = run(root, DEMO, version)
    assert run(root, DEMO, version) == report
    assert sum(sum(pair) for pair in report.folds) == report.eligible
    assert all(c.churn is None for d in report.distributions for c in d.cells)
    with TestClient(create_app(Settings(data_root=root, public_datasets=[DEMO]))) as client:
        assert client.get(f"/api/v1/analytics?dataset={DEMO}").json() is None
    with TestClient(
        create_app(Settings(data_root=root, public_datasets=[DEMO], analytics_datasets=[DEMO]))
    ) as client:
        res = client.get(f"/api/v1/analytics?dataset={DEMO}")
        assert res.status_code == 200 and res.json()["eligible"] == report.eligible
        assert all(k not in res.text for k in ("record_id", "members", "checksums", str(root)))
        assert client.get(f"/api/v1/analytics?dataset={DEMO}&version=no").status_code == 422
        assert client.get(f"/api/v1/analytics?dataset={DEMO}&version={'0' * 24}").status_code == 404
    folder, _ = identity(root, DEMO, version)
    (folder / "folds.json").write_text("corrupt")
    with pytest.raises(ValueError, match="corruption"):
        verify_artifacts(root, DEMO, version)
