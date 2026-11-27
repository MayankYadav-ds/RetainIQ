"""The only analysis component permitted to project held-out predictor vectors."""

import json
from pathlib import Path

from retainiq.data.contract import APPROVED, NAMES, digest, encoded
from retainiq.data.registry import read_manifest, verify

POLICY = "quarantine-projected-v1"


def key(row: dict[str, int], names: list[str]) -> str:
    return digest(encoded([row[n] for n in names]))


def audit(root: Path, dataset: str, version: str) -> tuple[dict[str, int], set[int]]:
    m = verify(root, dataset, version)
    folder, _ = read_manifest(root, dataset, version)
    # Role files interleave labels with inputs. Select only ordinals.
    members = {}
    for role in ("development", "holdout"):
        members[role] = {
            json.loads(line)["record_id"]
            for line in (folder / (role + ".jsonl")).read_bytes().splitlines()
        }
    dev, final = members["development"], members["holdout"]
    if (
        len(dev) != m.development
        or len(final) != m.holdout
        or dev & final
        or dev | final != set(range(1, m.row_count + 1))
    ):
        raise ValueError("partition_identity")
    vectors: dict[int, tuple[str, str]] = {}
    with (folder / "records.jsonl").open("rb") as stream:
        for line in stream:
            record = json.loads(line)
            rid = record["record_id"]
            predictors = {n: record[n] for n in NAMES[:-1]}
            vectors[rid] = (key(predictors, NAMES[:-1]), key(predictors, APPROVED))
    shared = [{vectors[i][j] for i in dev} & {vectors[i][j] for i in final} for j in (0, 1)]
    if shared[0]:
        raise ValueError("full_vector_overlap")
    quarantine = {i for i in dev if vectors[i][1] in shared[1]}
    return {
        "development": len(dev),
        "holdout": len(final),
        "shared_full": 0,
        "shared_approved": len(shared[1]),
        "affected_dev": len(quarantine),
        "affected_holdout": sum(vectors[i][1] in shared[1] for i in final),
    }, quarantine
