"""Health endpoint contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class LiveResponse(BaseModel):
    """Process liveness response."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    """Application readiness response."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["ready"] = "ready"

