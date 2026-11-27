"""Source-specific contracts. Insertion order is canonical column order."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

UCI = "uci_iranian_churn"
DEMO = "synthetic_churn_fixture"
PAGE = "https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset"
URL = "https://archive.ics.uci.edu/static/public/563/iranian+churn+dataset.zip"
ZIP_SHA = "696c3a1812267980751f30d19193a1b430ac4ad76172bb089e664c96813ead66"
CSV_SHA = "90d5fb6bd1630cd4de4b4d28fcf8b4cb92a8f6ab7484605b0799d47386f7dbe1"
TARGET = "Month-12 churn state following first-nine-month aggregates"
CITATION = "Iranian Churn [Dataset]. (2020). UCI Machine Learning Repository. DOI 10.24432/C5JW3Z"
HEADERS = [
    "Call  Failure",
    "Complains",
    "Subscription  Length",
    "Charge  Amount",
    "Seconds of Use",
    "Frequency of use",
    "Frequency of SMS",
    "Distinct Called Numbers",
    "Age Group",
    "Tariff Plan",
    "Status",
    "Age",
    "Customer Value",
    "Churn",
]
NAMES = ["_".join(h.lower().split()) for h in HEADERS]
CATEGORIES = {
    "complains": [0, 1],
    "age_group": list(range(1, 6)),
    "tariff_plan": [1, 2],
    "status": [1, 2],
    "churn": [0, 1],
}
RESTRICTED = {
    "status": "excluded",
    "customer_value": "requires further evidence",
    "age": "excluded",
    "age_group": "excluded",
    "charge_amount": "conditionally approved",
    "churn": "excluded",
}
APPROVED = [n for n in NAMES if n not in RESTRICTED]
CAPABILITIES = {
    k: k == "snapshot_classification"
    for k in [
        "snapshot_classification",
        "point_in_time_verification",
        "longitudinal_features",
        "temporal_holdout",
        "exact_horizons",
        "survival_analysis",
        "intervention_effects",
        "monetary_revenue",
    ]
}
PIPELINE = "1.0"
SEED = 20261127
FILES = ("records.jsonl", "development.jsonl", "holdout.jsonl", "quality.json", "quality.md")


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def encoded(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def version_for(dataset: str, raw: str) -> str:
    return digest(encoded([dataset, raw, PIPELINE, SEED]))[:24]


def checked_id(dataset: str) -> str:
    if dataset not in (UCI, DEMO):
        raise ValueError("unknown_dataset")
    return dataset


def file_sha(p: Path) -> str:
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, allow_inf_nan=False)


class Column(Contract):
    name: str
    dtype: Literal["integer", "number"]


def schema_columns() -> list[Column]:
    return [Column(name=n, dtype="number" if n == "customer_value" else "integer") for n in NAMES]


class Manifest(Contract):
    dataset_name: Literal["uci_iranian_churn", "synthetic_churn_fixture"]
    source: str
    license: str
    attribution: str
    version: str = Field(pattern="^[0-9a-f]{24}$")
    sha256: str = Field(pattern="^[0-9a-f]{64}$")
    acquired_at: AwareDatetime
    source_file_name: str
    source_bytes: int = Field(gt=0, le=2000000)
    columns: list[Column] = Field(alias="schema")
    prediction_target: Literal["churn"] = "churn"
    target_definition: Literal["Month-12 churn state following first-nine-month aggregates"] = (
        TARGET  # type: ignore[assignment]
    )
    observation_window: str = "First nine months"
    outcome_window: str = "State at end of month twelve; event date unavailable"
    supported_prediction_horizons_days: list[int] = Field(default_factory=list, max_length=0)
    provenance: str
    known_limitations: list[str]
    identifier_available: Literal[False] = False
    privacy: Literal["local row data; approved aggregates only"] = (
        "local row data; approved aggregates only"
    )
    schema_version: Literal[1] = 1
    pipeline_version: Literal["1.0"] = "1.0"
    split_seed: Literal[20261127] = 20261127
    holdout_fraction: Literal["1/5"] = "1/5"
    row_count: int = Field(gt=1, le=10000)
    feature_count: Literal[13] = 13
    development: int = Field(gt=0)
    holdout: int = Field(gt=0)
    artifact_checksums: dict[str, str]
    processed_sha256: str
    validation_status: Literal["passed_with_warnings", "passed"]

    @model_validator(mode="after")
    def consistent(self) -> "Manifest":
        if (
            self.version != version_for(self.dataset_name, self.sha256)
            or self.development + self.holdout != self.row_count
            or self.columns != schema_columns()
        ):
            raise ValueError("inconsistent_manifest")
        if (
            set(self.artifact_checksums) != set(FILES)
            or self.processed_sha256 != self.artifact_checksums["records.jsonl"]
        ):
            raise ValueError("invalid_artifact_inventory")
        if self.dataset_name == UCI and (
            self.sha256 not in (CSV_SHA, ZIP_SHA)
            or self.source != URL
            or self.license != "CC BY 4.0"
            or self.attribution != CITATION
        ):
            raise ValueError("unverified_source")
        if self.acquired_at.utcoffset() != timedelta(0):
            raise ValueError("receipt_requires_utc")
        if any(
            len(h) != 64 or any(c not in "0123456789abcdef" for c in h)
            for h in self.artifact_checksums.values()
        ):
            raise ValueError("invalid_artifact_digest")
        if self.dataset_name == UCI:
            expected = (
                (41943, "iranian+churn+dataset.zip")
                if self.sha256 == ZIP_SHA
                else (131728, "Customer Churn.csv")
            )
            if (self.source_bytes, self.source_file_name) != expected or self.row_count != 3150:
                raise ValueError("source_inventory_mismatch")
        return self
