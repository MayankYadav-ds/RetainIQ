"""Input contract and configured in-memory inference."""

import threading
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from threadpoolctl import threadpool_limits

from .final import receipt
from .protocol import BANDS
from .registry import load_model

Count = Annotated[int, Field(strict=True, ge=0, le=2**53 - 1)]
TARGET = "Month-twelve churn state using first-nine-month aggregates"
LIMITATIONS = "Snapshot benchmark. Exact daily horizons, causal effects and production calibration are unverified."


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    call_failure: Count
    complains: Literal[0, 1]
    subscription_length: Count
    seconds_of_use: Count
    frequency_of_use: Count
    frequency_of_sms: Count
    distinct_called_numbers: Count
    tariff_plan: Literal[1, 2]

    @field_validator("complains", "tariff_plan", mode="before")
    @classmethod
    def check_category(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("integer_category_required")
        return value


class Prediction(BaseModel):
    model: str
    feature_version: str
    feature_set: str
    benchmark: str
    raw_probability: float
    probability: float
    threshold: float
    predicted_class: Literal[0, 1]
    risk_tier: str
    warnings: list[str]
    target: str = TARGET
    limitations: str = LIMITATIONS


class Service:
    def __init__(self, root: Path, model_id: str) -> None:
        self.manifest, self.fitted, self.calibration = load_model(root, model_id)
        self.evaluation = receipt(root, self.manifest)
        self.lock = threading.BoundedSemaphore(1)

    def predict(self, inputs: list[Input]) -> list[Prediction]:
        if not self.lock.acquire(timeout=2):
            raise TimeoutError("prediction_capacity")
        try:
            rows = [x.model_dump() for x in inputs]
            with threadpool_limits(limits=1):
                scores = self.fitted.scores(rows)
            identity = self.manifest["identity"]
            results = []
            for row, raw in zip(rows, scores, strict=True):
                p = self.calibration.apply(raw)
                band = max((name for name, low in BANDS.items() if p >= low), key=BANDS.__getitem__)
                warnings = [
                    f"{k} is outside the observed development range"
                    for k, v in row.items()
                    if not identity["ranges"][k][0] <= v <= identity["ranges"][k][1]
                ]
                results.append(
                    Prediction(
                        model=self.manifest["model"],
                        feature_version=self.fitted.state.schema,
                        feature_set=self.fitted.state.fs,
                        benchmark=identity["cohort"]["dataset"],
                        raw_probability=raw,
                        probability=p,
                        threshold=identity["threshold"],
                        predicted_class=1 if p >= identity["threshold"] else 0,
                        risk_tier=band,
                        warnings=warnings,
                    )
                )
            return results
        finally:
            self.lock.release()
