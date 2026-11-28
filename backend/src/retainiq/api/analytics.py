from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from retainiq.analysis.features import CATALOG, SETS, VERSION
from retainiq.analysis.registry import read_report
from retainiq.analysis.stats import Report
from retainiq.core.config import Settings
from retainiq.data.contract import APPROVED, RESTRICTED
from retainiq.data.registry import versions


class FeatureCatalog(BaseModel):
    schema_version: str
    approved: list[str]
    excluded: dict[str, str]
    derived: dict[str, tuple[str, str, str]]
    sets: dict[str, list[str]]


def router(settings: Settings) -> APIRouter:
    routes = APIRouter(prefix="/api/v1")

    @routes.get("/analytics", response_model=Report | None)
    def analytics(
        dataset: Literal["uci_iranian_churn", "synthetic_churn_fixture"] = "uci_iranian_churn",
        version: Annotated[str | None, Query(pattern="^[0-9a-f]{24}$")] = None,
    ) -> Report | None:
        if dataset not in settings.analytics_datasets or dataset not in settings.public_datasets:
            return None
        keys = versions(settings.data_root, dataset)
        if version is not None and version not in keys:
            raise HTTPException(404)
        if not keys:
            return None
        try:
            report = read_report(settings.data_root, dataset, version or keys[0])
        except FileNotFoundError:
            return None
        except (ValueError, TypeError, KeyError, OSError):
            raise HTTPException(503) from None
        # Avoid publishing a combination of aggregate slices on very small real datasets.
        if dataset == "uci_iranian_churn" and report.eligible < 100:
            return None
        return report

    @routes.get("/features")
    def catalog() -> FeatureCatalog:
        return FeatureCatalog(
            schema_version=VERSION,
            approved=APPROVED,
            excluded=RESTRICTED | {"record_id": "traceability only"},
            derived=CATALOG,
            sets=SETS,
        )

    return routes
