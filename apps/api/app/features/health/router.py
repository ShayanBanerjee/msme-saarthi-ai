"""Liveness and readiness HTTP routes."""

from fastapi import APIRouter, status

from app.features.health.schemas import LiveResponse, ReadyResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=LiveResponse, status_code=status.HTTP_200_OK)
async def liveness() -> LiveResponse:
    """Report that the API process can serve requests."""
    return LiveResponse()


@router.get("/ready", response_model=ReadyResponse, status_code=status.HTTP_200_OK)
async def readiness() -> ReadyResponse:
    """Report readiness; no external dependencies exist in this bootstrap."""
    return ReadyResponse()

