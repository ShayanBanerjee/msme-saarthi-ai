"""Application-owned identity dependencies."""

from typing import Annotated, cast

from fastapi import Depends, Request, status

from app.core.errors import AppError
from app.features.auth.schemas import AuthenticatedUserResponse
from app.features.auth.service import AuthService


def get_auth_service(request: Request) -> AuthService:
    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        raise AppError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="identity_unavailable",
            title="Identity service unavailable",
            detail="Account services are not configured for this environment.",
        )
    return cast(AuthService, service)


async def current_user(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUserResponse:
    session_secret = request.cookies.get(request.app.state.settings.session_cookie_name)
    user = await service.authenticate(session_secret)
    if user is None:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="authentication_required",
            title="Authentication required",
            detail="Sign in to continue.",
        )
    return user
