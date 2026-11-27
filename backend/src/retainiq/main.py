import re
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.responses import Response

from retainiq import __version__
from retainiq.api.contracts import ErrorResponse, Health, Readiness, Version
from retainiq.core.config import Settings
from retainiq.core.logging import configure_logging
from retainiq.infrastructure.database import build_engine, probe


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    logger = configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.initialized = False
        app.state.engine = build_engine(config.database_url)
        try:
            # Remain live but not ready when the database is unavailable.
            try:
                app.state.initialized = await run_in_threadpool(probe, app.state.engine)
            except SQLAlchemyError:
                logger.warning("database_initialization_failed")
            yield
        finally:
            app.state.initialized = False
            app.state.engine.dispose()

    app = FastAPI(
        title="RetainIQ",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if config.environment != "production" else None,
        redoc_url=None,
    )
    app.state.initialized = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    def error(request: Request, status: int, code: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": getattr(request.state, "request_id", "unavailable"),
                }
            },
        )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            supplied if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", supplied) else uuid4().hex
        )
        start = time.perf_counter()
        try:
            if request.url.hostname in config.allowed_hosts:
                response = await call_next(request)
            else:
                response = error(request, 400, "invalid_host", "Host is not allowed")
        except Exception:
            logger.error("unhandled_request_error", extra={"request_id": request.state.request_id})
            response = error(request, 500, "internal_error", "An internal error occurred")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        logger.info(
            "request_completed",
            extra={
                "request_id": request.state.request_id,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error(request, exc.status_code, "http_error", "Request could not be completed")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error(request, 422, "validation_error", "Request validation failed")

    @app.get("/", response_model=Version)
    def root() -> Version:
        return Version(version=__version__)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health()

    @app.get("/ready", response_model=Readiness, responses={503: {"model": ErrorResponse}})
    def ready(request: Request) -> Readiness | JSONResponse:
        try:
            if not probe(request.app.state.engine):
                return error(request, 503, "not_ready", "Required resources unavailable")
            request.app.state.initialized = True
        except (SQLAlchemyError, AttributeError):
            return error(request, 503, "not_ready", "Required resources unavailable")
        return Readiness()

    @app.get("/api/v1/version", response_model=Version)
    def version() -> Version:
        return Version(version=__version__)

    return app
