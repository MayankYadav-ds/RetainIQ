from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from fastapi import Path as PathParam
from pydantic import BaseModel

from retainiq.core.config import Settings
from retainiq.data.contract import (
    CAPABILITIES,
    CITATION,
    NAMES,
    PAGE,
    RESTRICTED,
    UCI,
    file_sha,
)
from retainiq.data.quality import Quality
from retainiq.data.registry import read_manifest, versions


class Summary(BaseModel):
    dataset: str
    provenance: str
    source: str
    attribution: str
    license: str
    version: str
    rows: int
    features: int
    churn: int
    retained: int
    missing: int
    warnings: dict[str, int]
    eligibility: dict[str, str]
    capabilities: dict[str, bool]


Dataset = Literal["uci_iranian_churn", "synthetic_churn_fixture"]


def router(settings: Settings) -> APIRouter:
    routes = APIRouter(prefix="/api/v1/datasets", tags=["Dataset metadata"])

    def allowed(dataset: Dataset) -> list[str]:
        if dataset not in settings.public_datasets:
            raise HTTPException(404)
        return versions(settings.data_root, dataset)

    def summary(dataset: Dataset, v: str) -> Summary:
        if v not in allowed(dataset):
            raise HTTPException(404)
        folder, m = read_manifest(settings.data_root, dataset, v)
        path = folder / "quality.json"
        if path.stat().st_size > 100000 or file_sha(path) != m.artifact_checksums["quality.json"]:
            raise HTTPException(503)
        q = Quality.model_validate_json(path.read_bytes())
        warnings = {
            k: sum(i.affected_rows for i in q.issues if i.rule == k)
            for k in (
                "exact_duplicates",
                "predictor_duplicates",
                "conflicting_labels",
                "documented_range",
                "extreme",
                "constant",
                "near_constant",
            )
            if any(i.rule == k for i in q.issues)
        }
        return Summary(
            dataset=dataset,
            provenance="UCI benchmark" if dataset == UCI else "Synthetic fixture",
            source=PAGE if dataset == UCI else "Built-in deterministic fixture",
            attribution=CITATION if dataset == UCI else "RetainIQ",
            license="CC BY 4.0" if dataset == UCI else "MIT",
            version=v,
            rows=m.row_count,
            features=m.feature_count,
            churn=q.target_counts["1"],
            retained=q.target_counts["0"],
            missing=q.missing,
            warnings=warnings,
            eligibility={n: RESTRICTED.get(n, "approved") for n in NAMES[:-1]},
            capabilities=CAPABILITIES,
        )

    @routes.get("")
    def catalog() -> list[Summary]:
        results = []
        for d in settings.public_datasets:
            keys = allowed(d)
            if keys:
                results.append(summary(d, keys[0]))
        return results

    @routes.get("/{dataset}")
    def detail(dataset: Dataset) -> Summary:
        keys = allowed(dataset)
        if not keys:
            raise HTTPException(404)
        return summary(dataset, keys[0])

    @routes.get("/{dataset}/versions")
    def history(dataset: Dataset) -> list[str]:
        return allowed(dataset)

    @routes.get("/{dataset}/versions/{version}/quality")
    def quality(
        dataset: Dataset, version: Annotated[str, PathParam(pattern="^[a-f0-9]{24}$")]
    ) -> Summary:
        return summary(dataset, version)

    return routes
