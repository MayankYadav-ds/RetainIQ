from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from retainiq.data.registry import default_root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RETAINIQ_", env_file=".env", extra="ignore")
    environment: Literal["development", "production", "test"] = "development"
    data_root: Path = default_root()
    public_datasets: list[Literal["uci_iranian_churn", "synthetic_churn_fixture"]] = Field(
        default=["uci_iranian_churn"], max_length=2
    )
    analytics_datasets: list[Literal["uci_iranian_churn", "synthetic_churn_fixture"]] = Field(
        default_factory=list, max_length=2
    )
    database_url: str = "sqlite:///./retainiq.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]

    @field_validator("database_url")
    @classmethod
    def supported_database(cls, value: str) -> str:
        if not value.startswith(("sqlite:///", "postgresql+psycopg://")):
            raise ValueError("Use SQLite or an explicitly installed PostgreSQL psycopg driver")
        return value

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or "*" in value:
                raise ValueError("CORS requires explicit HTTP(S) origins")
            if parsed.path or parsed.query or parsed.fragment or parsed.username:
                raise ValueError("CORS origin must not contain paths or credentials")
        return values

    @field_validator("allowed_hosts")
    @classmethod
    def explicit_hosts(cls, values: list[str]) -> list[str]:
        if not values or any("*" in v or not v or "/" in v for v in values):
            raise ValueError("Explicit allowed hosts are required")
        return values

    @model_validator(mode="after")
    def production_boundary(self) -> "Settings":
        if self.environment == "production":
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError("Production CORS requires HTTPS")
            if "testserver" in self.allowed_hosts:
                raise ValueError("Production must explicitly configure allowed hosts")
        return self
