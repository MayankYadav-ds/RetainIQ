"""Local operator CLI. Training and holdout access are separate actions."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from retainiq.data.contract import DEMO, UCI
from retainiq.data.registry import default_root

from .benchmark import benchmark, load_benchmark
from .cohort import cohort
from .final import evaluate_final
from .inference import Input, Service
from .metrics import chart_data
from .protocol import PROTOCOL_SHA, SPEC
from .registry import freeze, load_model, models


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=[
            "protocol",
            "benchmark",
            "compare",
            "freeze",
            "evaluate-final",
            "models",
            "inspect",
            "verify",
            "predict",
        ],
    )
    p.add_argument("--root", type=Path, default=default_root())
    p.add_argument("--dataset", choices=[UCI, DEMO], default=UCI)
    p.add_argument("--version")
    p.add_argument("--view")
    p.add_argument("--experiment")
    p.add_argument("--model")
    p.add_argument("--input", type=Path, help="Local JSON for predict")
    p.add_argument("--ack-final", action="store_true")
    p.add_argument("--quick", action="store_true", help="Only for the synthetic fixture")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--detailed",
        action="store_true",
        help="Compute aggregate diagnostics for all stored OOF predictions",
    )
    a = p.parse_args()
    try:
        result: Any
        if a.quick and a.dataset != DEMO:
            raise ValueError("quick_requires_synthetic")
        if a.command == "protocol":
            result = {"specification": SPEC, "sha": PROTOCOL_SHA}
        elif a.command == "models":
            result = [
                {"model": r["model"], "family": r["identity"]["family"]} for r in models(a.root)
            ]
        elif a.command in ("benchmark", "freeze"):
            if not a.version or not a.view:
                raise ValueError("version_and_view_required")
            c = cohort(a.root, a.dataset, a.version, a.view)
            if a.command == "benchmark":
                result = benchmark(a.root, c, a.quick)
            elif a.experiment:
                result = freeze(a.root, c, a.experiment)
            else:
                raise ValueError("experiment_required")
        elif a.command == "compare":
            if not a.experiment:
                raise ValueError("experiment_required")
            folder, result = load_benchmark(a.root, a.experiment)
            if a.detailed:
                oof = json.loads((folder / "oof.json").read_bytes())
                result["diagnostics"] = {
                    family: chart_data(row["y"], row["raw"], row["probability"])
                    for family, row in oof.items()
                }
        elif not a.model:
            raise ValueError("model_required")
        elif a.command == "evaluate-final":
            result = evaluate_final(a.root, a.model, a.ack_final)
        elif a.command == "predict":
            if not a.input or a.input.stat().st_size > 4096:
                raise ValueError("input_required")
            result = (
                Service(a.root, a.model)
                .predict([Input.model_validate_json(a.input.read_bytes())])[0]
                .model_dump()
            )
        else:
            result = load_model(a.root, a.model)[0]
        print(json.dumps(result, indent=None if a.json else 2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        reason = str(exc)
        print(
            json.dumps({"error": reason if reason.isidentifier() else type(exc).__name__}),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
