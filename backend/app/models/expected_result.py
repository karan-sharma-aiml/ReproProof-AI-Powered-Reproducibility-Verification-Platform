"""Expected research metric values used for verification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MetricName = Literal[
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "loss",
    "mse",
    "mae",
    "custom_numeric",
]


class ExpectedResult(BaseModel):
    """Expected numeric outcome and comparison tolerance."""

    model_config = ConfigDict(frozen=True)

    expected_value: float
    metric_name: MetricName
    tolerance: float = Field(default=0.0, ge=0)
    metrics: dict[str, float] = Field(default_factory=dict)
    percentage_tolerance: float | None = Field(default=None, ge=0)
