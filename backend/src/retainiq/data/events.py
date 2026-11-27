"""Contract for future event adapters. No longitudinal ingestion is implemented."""

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .contract import Contract


class Event(Contract):
    customer_id: str = Field(min_length=1)
    entity: Literal[
        "customer",
        "subscription",
        "usage",
        "billing",
        "support",
        "churn",
        "intervention",
        "outcome",
    ]
    occurred_at: AwareDatetime
    available_at: AwareDatetime
    assignment_id: str | None = None
    cost_minor_units: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern="^[A-Z]{3}$")

    @model_validator(mode="after")
    def consistent(self) -> "Event":
        if self.available_at < self.occurred_at:
            raise ValueError("availability_precedes_event")
        if self.entity in ("intervention", "outcome") and not self.assignment_id:
            raise ValueError("assignment_required")
        if (self.cost_minor_units is None) != (self.currency is None):
            raise ValueError("currency_required")
        return self

    def observable(self, cutoff: AwareDatetime) -> bool:
        return self.occurred_at <= cutoff and self.available_at <= cutoff


class OutcomeWindow(Contract):
    cutoff: AwareDatetime
    end: AwareDatetime
    observed_until: AwareDatetime

    @model_validator(mode="after")
    def positive_window(self) -> "OutcomeWindow":
        if self.end <= self.cutoff:
            raise ValueError("invalid_outcome_window")
        return self

    @property
    def censored(self) -> bool:
        return self.observed_until < self.end
