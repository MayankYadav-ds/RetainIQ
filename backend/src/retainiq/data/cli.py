"""Operator-only pipeline CLI."""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Literal, cast

import httpx

from .acquire import acquire, csv_bytes
from .contract import DEMO, UCI, URL
from .quality import InvalidData, normalize
from .registry import default_root, ingest, known_raw, raw_object, read_manifest, verify, versions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire, validate and inspect local snapshot versions"
    )
    parser.add_argument(
        "command",
        choices=[
            "sources",
            "acquire",
            "ingest",
            "validate",
            "profile",
            "list",
            "inspect",
            "verify",
            "run",
        ],
    )
    parser.add_argument("--dataset", choices=[UCI, DEMO], default=UCI)
    parser.add_argument(
        "--file", type=Path, help="Offline official ZIP or original CSV (pinned bytes)"
    )
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--version", help="Published version for inspect, verify or profile")
    parser.add_argument("--json", action="store_true", help="Compact machine-readable JSON")
    a = parser.parse_args()
    dataset = cast(Literal["uci_iranian_churn", "synthetic_churn_fixture"], a.dataset)
    result: object
    try:
        if a.version and a.command not in ("inspect", "verify", "profile"):
            raise ValueError("version_option_not_supported")
        if a.file and a.command not in ("acquire", "run"):
            raise ValueError("file_option_not_supported")
        if a.command == "sources":
            result = {UCI: URL, DEMO: "synthetic built-in fixture"}
        elif a.command == "list":
            result = {name: versions(a.root, name) for name in (UCI, DEMO)}
        elif a.command == "acquire":
            result = {"sha256": acquire(a.root, dataset, a.file)}
        elif a.command == "validate":
            _, raw = raw_object(a.root, dataset)
            result = {"validated_rows": len(normalize(csv_bytes((raw / "source").read_bytes())))}
        elif a.command in ("run", "ingest"):
            sha = None
            if a.command == "run" and (
                a.file
                or not any((a.root / "raw" / dataset / k).exists() for k in known_raw(dataset))
            ):
                sha = acquire(a.root, dataset, a.file)
            result = ingest(a.root, dataset, sha).model_dump(mode="json", by_alias=True)
        elif a.command == "profile":
            verify(a.root, dataset, a.version)
            folder, _ = read_manifest(a.root, dataset, a.version)
            result = (
                json.loads((folder / "quality.json").read_bytes())
                if a.json
                else (folder / "quality.md").read_text(encoding="utf-8")
            )
        else:
            result = verify(a.root, dataset, a.version).model_dump(mode="json", by_alias=True)
    except (ValueError, OSError, zipfile.BadZipFile, httpx.HTTPError) as exc:
        msg = (
            str(exc) if type(exc) is ValueError and str(exc).isidentifier() else type(exc).__name__
        )
        print(
            json.dumps(
                {
                    "error": msg,
                    "issues": [i.model_dump() for i in exc.issues]
                    if isinstance(exc, InvalidData)
                    else [],
                }
            ),
            file=sys.stderr,
        )
        return 1
    print(result if isinstance(result, str) else json.dumps(result, indent=None if a.json else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
