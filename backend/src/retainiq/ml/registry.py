"""Trusted local artifact registry. No pickle or upload interface."""

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import skops.io as sio
from threadpoolctl import threadpool_limits

from retainiq.analysis.features import SETS, FoldState, fingerprint
from retainiq.data.acquire import publish_dir, staging
from retainiq.data.contract import APPROVED, digest, encoded, file_sha

from .benchmark import champion, dependencies, identifier, load_benchmark
from .cohort import Cohort
from .protocol import BANDS, GRIDS, PROTOCOL_SHA
from .train import Calibration, Fitted, make, train

# Reviewed for the pinned HistGradientBoosting implementation only.
TRUSTED_HIST = {
    "sklearn._loss.link.Interval",
    "sklearn._loss.link.LogitLink",
    "sklearn._loss.loss.HalfBinomialLoss",
    "sklearn.ensemble._hist_gradient_boosting.binning._BinMapper",
    "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
}
FILENAMES = {"xgboost": "model.ubj", "lightgbm": "model.txt"}
MODEL_TYPES = {
    "logistic": "LogisticRegression",
    "tree": "DecisionTreeClassifier",
    "forest": "RandomForestClassifier",
    "extra_trees": "ExtraTreesClassifier",
    "hist_gradient": "HistGradientBoostingClassifier",
}


def save(model: Any, family: str, folder: Path) -> Path:
    path = folder / FILENAMES.get(family, "model.skops")
    if family == "xgboost":
        model.save_model(path)
    elif family == "lightgbm":
        model.booster_.save_model(str(path))
    else:
        sio.dump(model, path)
    return path


class LightAdapter:
    feature_name_ = True

    def __init__(self, path: Path) -> None:
        from lightgbm import Booster

        self.booster_ = Booster(model_file=str(path))


def restore(path: Path, family: str) -> Any:
    if family == "xgboost":
        model = make(family, {})
        model.load_model(path)
        return model
    if family == "lightgbm":
        return LightAdapter(path)
    blob = path.read_bytes()
    unknown = set(sio.get_untrusted_types(data=blob))
    allowed = TRUSTED_HIST if family == "hist_gradient" else set()
    if not unknown <= allowed:
        raise ValueError("unapproved_serialized_types")
    model = sio.loads(blob, trusted=sorted(allowed))
    if type(model).__name__ != MODEL_TYPES[family] or not type(model).__module__.startswith(
        "sklearn."
    ):
        raise ValueError("unexpected_estimator")
    return model


def load_model(root: Path, model_id: str) -> tuple[dict[str, Any], Fitted, Calibration]:
    loc = root / "ml" / "models" / identifier(model_id)
    if (loc / "freeze.json").stat().st_size > 30000:
        raise ValueError("freeze_size")
    manifest: dict[str, Any] = json.loads((loc / "freeze.json").read_bytes())
    ref = manifest["identity"]
    family = ref["family"]
    if (
        manifest["model"] != model_id
        or digest(encoded(ref))[:24] != model_id
        or ref["protocol"] != PROTOCOL_SHA
        or ref["dependencies"] != dependencies()
        or family not in GRIDS
        or manifest["selection"] != "frozen"
    ):
        raise ValueError("invalid_freeze")
    path = loc / FILENAMES.get(family, "model.skops")
    if path.stat().st_size > 8000000 or file_sha(path) != ref["sha"]:
        raise ValueError("model_checksum")
    state = FoldState(**ref["preprocessing"])
    calibration = Calibration(**ref["calibration"])
    if state.fs not in SETS or state.schema != fingerprint(state.fs):
        raise ValueError("feature_fingerprint")
    names = [n for n in SETS[state.fs] if n != "tariff_plan"] + [
        "tariff_contract",
        "tariff_unknown",
    ]
    if (
        state.names != names
        or len(state.means) != len(names)
        or len(state.scales) != len(names)
        or not all(math.isfinite(x) for x in state.means + state.scales)
        or not all(s > 0 for s in state.scales)
    ):
        raise ValueError("invalid_preprocessing")
    if (
        calibration.method not in ("none", "sigmoid", "isotonic")
        or len(calibration.x) != len(calibration.y)
        or any(not math.isfinite(x) for x in calibration.x + calibration.y)
    ):
        raise ValueError("invalid_calibration")
    if calibration.method == "sigmoid" and len(calibration.x) != 1:
        raise ValueError("invalid_sigmoid")
    if calibration.method == "isotonic" and (
        not calibration.x
        or sorted(set(calibration.x)) != calibration.x
        or sorted(calibration.y) != calibration.y
        or any(not 0 <= x <= 1 for x in calibration.x + calibration.y)
    ):
        raise ValueError("invalid_isotonic")
    if ref["bands"] != BANDS or not 0.05 <= ref["threshold"] <= 0.95:
        raise ValueError("invalid_decision_policy")
    return manifest, Fitted(restore(path, family), state, ref["cohort"]["development"]), calibration


def freeze(root: Path, c: Cohort, experiment: str) -> dict[str, Any]:
    _, report = load_benchmark(root, experiment)
    if report["cohort"] != c.reference or (
        report["quick"] and c.reference["dataset"] != "synthetic_churn_fixture"
    ):
        raise ValueError("wrong_experiment")
    family = champion(report["leaderboard"])
    for old in models(root):
        if old["identity"]["experiment"] == experiment:
            return load_model(root, old["model"])[0]
    proof = train(c.data, family, -1, report["quick"])
    with staging(root) as temp:
        folder = temp / "frozen"
        folder.mkdir()
        artifact = save(proof.base.estimator, family, folder)
        if artifact.stat().st_size > 8000000:
            raise ValueError("artifact_size")
        restored = Fitted(restore(artifact, family), proof.base.state, proof.base.membership)
        with threadpool_limits(limits=1):
            expected = proof.base.scores(c.data.x)
            actual = restored.scores(c.data.x)
        error = max(abs(a - b) for a, b in zip(expected, actual, strict=True))
        if error > 1e-10:
            raise ValueError("round_trip_parity")
        ref = {
            "experiment": experiment,
            "protocol": PROTOCOL_SHA,
            "cohort": c.reference,
            "family": family,
            "preprocessing": asdict(proof.base.state),
            "choice": proof.evidence["choice"],
            "threshold": proof.threshold,
            "bands": BANDS,
            "calibration": asdict(proof.calibration),
            "sha": file_sha(artifact),
            "dependencies": dependencies(),
            "ranges": {
                n: [min(x[n] for x in c.data.x), max(x[n] for x in c.data.x)] for n in APPROVED
            },
        }
        model_id = digest(encoded(ref))[:24]
        result = {
            "model": model_id,
            "identity": ref,
            "selection": "frozen",
            "bytes": artifact.stat().st_size,
            "parity_error": error,
            "policy_brier": proof.evidence["brier"],
            "role_counts": proof.evidence["role_counts"],
            "fit_seconds": proof.evidence["seconds"],
        }
        (folder / "freeze.json").write_bytes(encoded(result))
        (folder / "training.json").write_bytes(encoded(proof.evidence))
        publish_dir(folder, root / "ml" / "models" / model_id)
    return load_model(root, model_id)[0]


def models(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted((root / "ml" / "models").glob("*/freeze.json")):
        try:
            identifier(path.parent.name)
            obj = json.loads(path.read_bytes())
            if obj["model"] == path.parent.name:
                result.append(obj)
        except (ValueError, OSError, KeyError):
            continue
    return result
