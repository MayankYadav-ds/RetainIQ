import argparse
import json
import sys
from pathlib import Path

from retainiq.data.contract import DEMO, UCI
from retainiq.data.registry import default_root

from .features import CATALOG, SETS
from .integrity import audit
from .registry import identity, run, verify_artifacts
from .view import folds, load


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit and analyze the eligible development partition"
    )
    parser.add_argument(
        "command",
        choices=[
            "audit-partitions",
            "create-folds",
            "profile",
            "associations",
            "features",
            "transform",
            "verify",
            "run",
        ],
    )
    parser.add_argument("--dataset", choices=[UCI, DEMO], default=UCI)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--root", type=Path, default=default_root(), help="Local dataset and analysis store"
    )
    parser.add_argument("--set", choices=list(SETS), default="FS01")
    parser.add_argument("--json", action="store_true")
    a = parser.parse_args()
    result: object
    try:
        if a.command == "audit-partitions":
            result = audit(a.root, a.dataset, a.version)[0]
        elif a.command == "create-folds":
            _, quarantine = audit(a.root, a.dataset, a.version)
            view = load(a.root, a.dataset, a.version, quarantine)
            member = folds(view)
            result = [
                [
                    sum(f == i and y == j for f, y in zip(member, view.y, strict=True))
                    for j in (0, 1)
                ]
                for i in range(5)
            ]
        elif a.command == "features":
            result = {
                "names": SETS[a.set],
                "derived": {k: v for k, v in CATALOG.items() if k in SETS[a.set]},
            }
        else:
            report = (
                run if a.command in ("run", "create-folds", "transform") else verify_artifacts
            )(a.root, a.dataset, a.version)
            if a.command == "profile" and not a.json:
                folder, _ = identity(a.root, a.dataset, a.version)
                print((folder / "report.md").read_text(encoding="utf8"))
                return 0
            result = {
                "associations": [r.model_dump() for r in report.associations],
                "create-folds": report.folds,
                "transform": {
                    "rows": report.eligible,
                    "names": SETS[a.set],
                    "parity": report.parity,
                },
            }.get(a.command, report.model_dump())
    except (ValueError, OSError, KeyError) as exc:
        print(
            json.dumps(
                {
                    "error": type(exc).__name__,
                    "reason": str(exc) if str(exc).isidentifier() else "analysis_unavailable",
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=None if a.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
