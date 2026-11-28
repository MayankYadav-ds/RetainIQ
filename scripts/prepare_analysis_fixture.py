"""Prepare the deterministic synthetic registry for browser validation."""

import os
import sys

import uvicorn

from retainiq.analysis.registry import run
from retainiq.data.acquire import acquire
from retainiq.data.contract import DEMO
from retainiq.data.registry import default_root, ingest

root = default_root()
acquire(root, DEMO)
manifest = ingest(root, DEMO)
run(root, DEMO, manifest.version)

if "--serve" in sys.argv:
    from retainiq.ml.benchmark import benchmark
    from retainiq.ml.cohort import cohort
    from retainiq.ml.final import evaluate_final
    from retainiq.ml.registry import freeze

    report = run(root, DEMO, manifest.version)
    c = cohort(root, DEMO, manifest.version, report.view_version)
    board = benchmark(root, c, quick=True)
    selected = freeze(root, c, board["experiment"])
    evaluate_final(root, selected["model"], True)
    os.environ["RETAINIQ_ACTIVE_MODEL"] = selected["model"]
    uvicorn.run("retainiq.main:create_app", factory=True, port=8000, access_log=False)
