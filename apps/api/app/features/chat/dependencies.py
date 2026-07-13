"""Fail-closed authentication and application-owned chat dependencies."""

from typing import Annotated, cast

from fastapi import Depends, Request

from app.features.auth.dependencies import current_user
from app.features.auth.schemas import AuthenticatedUserResponse
from app.features.chat.models import AuthenticatedActor
from app.features.chat.service import ChatService


async def require_actor(
    user: Annotated[AuthenticatedUserResponse, Depends(current_user)],
) -> AuthenticatedActor:
    """Resolve actor and tenant exclusively from the trusted server-side session."""
    return AuthenticatedActor(
        actor_id=user.id,
        tenant_id=user.tenant_id,
    )


def get_chat_service(request: Request) -> ChatService:
    """Resolve the application-scoped service initialized by the factory."""
    return cast(ChatService, request.app.state.chat_service)
