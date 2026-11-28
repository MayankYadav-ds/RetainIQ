"""Explicit one-shot evaluation. This is the only label-reading holdout path."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from threadpoolctl import threadpool_limits

from retainiq.analysis.integrity import key
from retainiq.data.acquire import publish_dir, staging
from retainiq.data.contract import APPROVED, UCI, digest, encoded, file_sha
from retainiq.data.registry import read_manifest, verify

from .benchmark import load_benchmark
from .metrics import bootstrap, chart_data, evaluate
from .registry import load_model


def receipt_path(root: Path, manifest: dict[str, Any]) -> Path:
    c = manifest["identity"]["cohort"]
    return root / "ml" / "evaluations" / digest(encoded([c["dataset"], c["holdout"]]))[:24]


def receipt(root: Path, m: dict[str, Any]) -> dict[str, Any]:
    path = receipt_path(root, m)
    obj: dict[str, Any] = json.loads((path / "receipt.json").read_bytes())
    content = obj["content"]
    if (
        obj["receipt"] != digest(encoded(content))
        or content["model"] != m["model"]
        or content["freeze_sha"] != digest(encoded(m))
        or content["rows_sha"] != file_sha(path / "local-predictions.json")
    ):
        raise ValueError("evaluation_receipt_mismatch")
    return obj


def evaluate_final(root: Path, model_id: str, ack: bool) -> dict[str, Any]:
    if not ack:
        raise ValueError("explicit_final_acknowledgment_required")
    manifest, fitted, calibration = load_model(root, model_id)
    identity = manifest["identity"]
    ref = identity["cohort"]
    dataset, version = ref["dataset"], ref["version"]
    _, board = load_benchmark(root, identity["experiment"])
    if (
        board["selected"] != identity["family"]
        or board["cohort"] != ref
        or manifest["parity_error"] > 1e-10
    ):
        raise ValueError("champion_not_verified")
    m = verify(root, dataset, version)
    folder, _ = read_manifest(root, dataset, version)
    source = folder / "holdout.jsonl"
    if file_sha(source) != ref["holdout"] or (dataset == UCI and m.holdout != 630):
        raise ValueError("holdout_integrity")
    ledger = receipt_path(root, manifest)
    if ledger.exists():
        return receipt(root, manifest)
    marker = ledger.with_suffix(".started")
    marker.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open("xb") as f:
            f.write(
                encoded(
                    {
                        "model": model_id,
                        "freeze_sha": digest(encoded(manifest)),
                        "started_at": datetime.now(UTC).isoformat(),
                    }
                )
            )
            f.flush()
            os.fsync(f.fileno())
    except FileExistsError as exc:
        raise ValueError("evaluation_already_started_manual_audit_required") from exc
    rows = [json.loads(line) for line in source.read_bytes().splitlines()]
    if len(rows) != m.holdout or len({r["record_id"] for r in rows}) != m.holdout:
        raise ValueError("holdout_membership")
    x = [r["features"] for r in rows]
    y = [r["target"] for r in rows]
    with threadpool_limits(limits=1):
        raw = fitted.scores(x)
    p = [calibration.apply(r) for r in raw]
    d = [int(q >= identity["threshold"]) for q in p]
    train_prev = 372 / 2480 if dataset == UCI else board["leaderboard"][0]["metrics"]["prevalence"]
    reference = evaluate(y, [train_prev] * len(y), [train_prev] * len(y), [0] * len(y))
    majority = evaluate(y, [0.0] * len(y), [0.0] * len(y), [0] * len(y))
    result = {
        "model": model_id,
        "freeze_sha": digest(encoded(manifest)),
        "holdout": ref["holdout"],
        "metrics": evaluate(y, raw, p, d),
        "reference": reference,
        "majority": majority,
        "charts": chart_data(y, raw, p),
        "threshold": identity["threshold"],
        "uncertainty": bootstrap(y, raw, p, d, [key(row, APPROVED) for row in x]),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    with staging(root) as temp:
        pub = temp / "evaluation"
        pub.mkdir()
        (pub / "local-predictions.json").write_bytes(encoded(dict(y=y, raw=raw, p=p, decisions=d)))
        result["rows_sha"] = file_sha(pub / "local-predictions.json")
        (pub / "receipt.json").write_bytes(
            encoded({"receipt": digest(encoded(result)), "content": result})
        )
        publish_dir(pub, ledger)
    if file_sha(source) != ref["holdout"]:
        raise ValueError("holdout_changed")
    return receipt(root, manifest)
