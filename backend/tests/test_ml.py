import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from retainiq.analysis.registry import run
from retainiq.core.config import Settings
from retainiq.data.acquire import acquire
from retainiq.data.contract import DEMO
from retainiq.data.registry import ingest, read_manifest
from retainiq.main import create_app
from retainiq.ml.benchmark import benchmark, load_benchmark
from retainiq.ml.cohort import cohort
from retainiq.ml.final import evaluate_final
from retainiq.ml.metrics import bootstrap, evaluate, policy, ranking
from retainiq.ml.registry import freeze, load_model


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    root = tmp_path_factory.mktemp("benchmark")
    acquire(root, DEMO)
    manifest = ingest(root, DEMO)
    analysis = run(root, DEMO, manifest.version)
    c = cohort(root, DEMO, manifest.version, analysis.view_version)
    board = benchmark(root, c, True)
    m = freeze(root, c, board["experiment"])
    return root, c, board, m


def test_known_metrics():
    y = [1, 0, 1, 0]
    p = [0.9, 0.6, 0.4, 0.1]
    r = evaluate(y, p, p, [1, 1, 0, 0])
    assert [r[k] for k in ("tp", "fp", "fn", "tn", "f1", "accuracy")] == [1, 1, 1, 1, 0.5, 0.5]
    assert r["brier"] == pytest.approx(0.185)
    assert r["auc"] == 0.75
    assert ranking(y, [0.3] * 4, 0.25)["lift"] == 2
    assert evaluate([0], [0.3], [0.3], [0])["auc"] is None
    with pytest.raises(ValueError):
        evaluate(y, [2.0] * 4, p, y)
    a = bootstrap(y, p, p, [1, 1, 0, 0], list("abcd"), 20)
    assert a == bootstrap(y, p, p, [1, 1, 0, 0], list("abcd"), 20)
    assert policy(y, p)[0] == 0.4


def test_nested_and_frozen(lab):
    root, c, board, m = lab
    folder, _ = load_benchmark(root, board["experiment"])
    rows = json.loads((folder / "oof.json").read_bytes())["logistic"]
    roles = json.loads((folder / "search.json").read_bytes())["logistic"]
    assert rows["ids"] == c.data.ids and len(rows["probability"]) == len(c.data.y)
    for i, fit in enumerate(roles):
        parts = fit["role_membership"]
        groups = [set(parts[k]) for k in ("core", "calibration", "policy")]
        outer = {rid for rid, f in zip(c.data.ids, c.outer, strict=True) if i == f}
        assert sum(map(len, [outer, *groups])) == len(outer.union(*groups)) == len(c.data.ids)
    assert m["parity_error"] <= 1e-10
    assert freeze(root, c, board["experiment"]) == m
    with pytest.raises(ValueError, match="view_mismatch"):
        cohort(root, DEMO, c.reference["version"], "invalid")
    with pytest.raises(ValueError, match="acknowledgment"):
        evaluate_final(root, m["model"], False)


def test_once_and_serving(lab):
    root, c, _, m = lab
    model = m["model"]
    row = c.data.x[0]
    with TestClient(create_app(Settings(data_root=root, active_model=model))) as client:
        assert client.get("/api/v1/models/active").json() is None
        assert client.post("/api/v1/predictions/single", json=row).status_code == 503
    folder, manifest = read_manifest(root, DEMO, c.reference["version"])
    source = folder / "holdout.jsonl"
    expected = source.read_bytes()
    result = evaluate_final(root, model, True)
    assert result == evaluate_final(root, model, True)
    assert len(expected) > 0 and source.read_bytes() == expected
    assert result["content"]["metrics"]["n"] == manifest.holdout
    with TestClient(
        create_app(Settings(data_root=root, active_model=model, prediction_batch_limit=2))
    ) as client:
        assert client.get("/ready").status_code == 200
        assert client.get("/api/v1/models/evaluation").json()["receipt"] == result["receipt"]
        one = client.post("/api/v1/predictions/single", json=row).json()
        assert one["model"] == model and 0 <= one["probability"] <= 1
        assert one["predicted_class"] == int(one["probability"] >= one["threshold"])
        assert client.post("/api/v1/predictions/batch", json={"rows": [row, row]}).json() == [
            one,
            one,
        ]
        for bad in (
            {**row, "churn": 1},
            {**row, "tariff_plan": 3},
            {**row, "complains": True},
            {**row, "seconds_of_use": "secret"},
        ):
            res = client.post("/api/v1/predictions/single", json=bad)
            assert res.status_code == 422 and "secret" not in res.text
        assert client.post("/api/v1/predictions/batch", json={"rows": [row] * 3}).status_code == 422
        assert client.post("/api/v1/predictions/single", content=b" " * 65537).status_code == 413
        assert "role_membership" not in client.get("/api/v1/models/benchmark").text
    path = Path(root / "ml" / "models" / model / "model.skops")
    original = path.read_bytes()
    try:
        path.write_bytes(b"corrupt")
        with pytest.raises(ValueError, match="checksum"):
            load_model(root, model)
        with pytest.raises(ValueError, match="checksum"):
            evaluate_final(root, model, True)
    finally:
        path.write_bytes(original)
