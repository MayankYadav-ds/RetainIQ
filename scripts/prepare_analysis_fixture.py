"""Prepare the deterministic synthetic registry for browser validation."""

from retainiq.analysis.registry import run
from retainiq.data.acquire import acquire
from retainiq.data.contract import DEMO
from retainiq.data.registry import default_root, ingest

root = default_root()
acquire(root, DEMO)
manifest = ingest(root, DEMO)
run(root, DEMO, manifest.version)
