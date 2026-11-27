import json
import logging

import pytest
from fastapi import Query
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from retainiq.core.config import Settings
from retainiq.core.logging import JsonFormatter
from retainiq.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(environment="test", database_url=f"sqlite:///{tmp_path}/test.db"))
    with TestClient(app) as client:
        yield client


def test_startup_and_shutdown(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path}/test.db"))
    assert not app.state.initialized
    with TestClient(app) as client:
        assert app.state.initialized
        assert client.get("/").json() == {"name": "RetainIQ", "version": "0.2.0", "phase": 1}
    assert not app.state.initialized


def test_health_and_version(client):
    assert client.get("/health").json() == {"status": "alive"}
    assert client.get("/api/v1/version").json()["version"] == "0.2.0"
    assert client.get("/ready").json() == {"status": "ready", "database": "reachable"}


def test_database_connectivity(client):
    with client.app.state.engine.connect() as connection:
        assert connection.execute(text("SELECT 40 + 2")).scalar_one() == 42


def test_readiness_failure_and_recovery(client, monkeypatch):
    def unavailable(engine):
        raise OperationalError("sensitive path", {}, Exception("secret"))

    with monkeypatch.context() as patch:
        patch.setattr("retainiq.main.probe", unavailable)
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "not_ready"
        assert "secret" not in response.text and "sensitive" not in response.text
        assert client.get("/health").json()["status"] == "alive"
    assert client.get("/ready").json()["database"] == "reachable"


def test_failed_initialization(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path}/missing/sub/db.sqlite"))
    with TestClient(app) as client:
        assert not app.state.initialized
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503


def test_uninitialized_resources():
    with TestClient(create_app()) as client:
        del client.app.state.engine
        assert client.get("/ready").status_code == 503
        # Restore engine so lifespan can dispose it.
        from retainiq.infrastructure.database import build_engine

        client.app.state.engine = build_engine("sqlite:///:memory:")


@pytest.mark.parametrize("value", ["x" * 65, "contains spaces", "<script>"])
def test_untrusted_request_ids(client, value):
    response = client.get("/health", headers={"X-Request-ID": value})
    assert response.headers["X-Request-ID"] != value
    assert len(response.headers["X-Request-ID"]) == 32


def test_correlation_and_error_envelope(client):
    response = client.get("/does-not-exist", headers={"X-Request-ID": "test_123-abc"})
    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "http_error",
        "message": "Request could not be completed",
        "request_id": "test_123-abc",
    }
    assert response.headers["X-Request-ID"] == "test_123-abc"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


def test_internal_errors_are_redacted(client):
    @client.app.get("/test-error")
    def fail():
        raise RuntimeError("password and filesystem path")

    response = client.get("/test-error")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "password" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_validation_is_redacted(client):
    @client.app.get("/test-input")
    def validate(count: int = Query(ge=1)):
        return {"count": count}

    response = client.get("/test-input?count=private-value")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "private-value" not in response.text


def test_cors(client):
    allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    denied = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in denied.headers
    assert "Access-Control-Allow-Credentials" not in allowed.headers


def test_host_rejected(client):
    response = client.get("/health", headers={"Host": "evil.example"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_host"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"environment": "unknown"},
        {"database_url": "mysql://unsafe"},
        {"cors_origins": ["*"]},
        {"cors_origins": ["http://localhost:5173/path"]},
        {"allowed_hosts": ["*"]},
        {"environment": "production"},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **kwargs)


def test_production_boundary():
    settings = Settings(
        environment="production",
        cors_origins=["https://demo.example"],
        allowed_hosts=["api.example"],
    )
    app = create_app(settings)
    with TestClient(app, base_url="https://api.example") as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/health").json()["status"] == "alive"


def test_logs_exclude_arbitrary_fields():
    record = logging.LogRecord(
        "test", logging.INFO, "secret/path", 1, "request_completed", (), None
    )
    record.password = "secret"
    parsed = json.loads(JsonFormatter().format(record))
    assert parsed["event"] == "request_completed"
    assert "secret" not in json.dumps(parsed)
