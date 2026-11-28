"""Bounded and explicitly enabled local benchmark inference routes."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from starlette.types import Message

from retainiq.core.config import Settings
from retainiq.ml.benchmark import load_benchmark
from retainiq.ml.inference import LIMITATIONS, TARGET, Input, Prediction, Service


class BodyLimit(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        handler = super().get_route_handler()

        async def limited(request: Request) -> Response:
            if request.method == "POST":
                chunks = bytearray()
                async for chunk in request.stream():
                    if len(chunks) + len(chunk) > 65536:
                        raise HTTPException(413)
                    chunks.extend(chunk)

                async def receive() -> Message:
                    return {"type": "http.request", "body": bytes(chunks), "more_body": False}

                request = Request(request.scope, receive)
            return await handler(request)

        return limited


class Batch(BaseModel):
    rows: list[Input] = Field(min_length=1, max_length=100)


class Model(BaseModel):
    model: str
    family: str
    feature_set: str
    calibration: str
    threshold: float
    experiment: str
    dataset: str
    target: str = TARGET
    limitations: str = LIMITATIONS


class Evidence(BaseModel):
    experiment: str
    selected: str
    leaderboard: list[dict[str, Any]]
    development: dict[str, Any]
    threshold_sweep: list[dict[str, float]]
    uncertainty: dict[str, Any]
    calibration_choices: list[dict[str, float]]


class Evaluation(BaseModel):
    receipt: str
    model: str
    metrics: dict[str, float | None]
    charts: dict[str, Any]
    uncertainty: dict[str, Any]
    threshold: float


def router(settings: Settings) -> APIRouter:
    routes = APIRouter(prefix="/api/v1", route_class=BodyLimit)
    service: Service | None = None
    board: Evidence | None = None
    if settings.active_model and settings.environment != "production":
        try:
            candidate = Service(settings.data_root, settings.active_model)
            ref = candidate.manifest["identity"]
            _, summary = load_benchmark(settings.data_root, ref["experiment"])
            board = Evidence.model_validate(summary)
            service = candidate
        except (ValueError, TypeError, RuntimeError, KeyError, OSError, ImportError):
            # Model availability must not change service health or leak local paths.
            pass

    @routes.get("/models/active")
    def active() -> Model | None:
        if service is None:
            return None
        m = service.manifest
        i = m["identity"]
        return Model(
            model=m["model"],
            family=i["family"],
            feature_set=i["choice"]["fs"],
            calibration=i["calibration"]["method"],
            threshold=i["threshold"],
            experiment=i["experiment"],
            dataset=i["cohort"]["dataset"],
        )

    @routes.get("/models")
    def models() -> list[Model]:
        value = active()
        return [] if value is None else [value]

    @routes.get("/models/benchmark")
    def benchmark() -> Evidence | None:
        return board

    @routes.get("/models/evaluation")
    def evaluation() -> Evaluation | None:
        if service is None:
            return None
        r = service.evaluation
        return Evaluation(receipt=r["receipt"], **r["content"])

    def predict(inputs: list[Input]) -> list[Prediction]:
        if service is None:
            raise HTTPException(503)
        try:
            return service.predict(inputs)
        except TimeoutError as exc:
            raise HTTPException(429) from exc

    @routes.post("/predictions/single")
    def single(item: Input) -> Prediction:
        return predict([item])[0]

    @routes.post("/predictions/batch")
    def batch(item: Batch) -> list[Prediction]:
        if len(item.rows) > settings.prediction_batch_limit:
            raise HTTPException(422)
        return predict(item.rows)

    return routes
