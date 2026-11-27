from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["alive"] = "alive"


class Readiness(BaseModel):
    status: Literal["ready"] = "ready"
    database: Literal["reachable"] = "reachable"


class Version(BaseModel):
    name: str = "RetainIQ"
    version: str
    phase: int = 1


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
