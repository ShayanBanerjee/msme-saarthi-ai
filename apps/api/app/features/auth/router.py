"""Self-service identity HTTP endpoints with secure server-side sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.errors import AppError
from app.features.auth.dependencies import current_user, get_auth_service
from app.features.auth.schemas import AuthenticatedUserResponse, LoginRequest, RegisterRequest
from app.features.auth.service import AuthService, IdentityConflictError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, request: Request, secret: str) -> None:
    settings = request.app.state.settings
    response.set_cookie(
        key=settings.session_cookie_name,
        value=secret,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="strict",
        max_age=settings.session_absolute_hours * 60 * 60,
        path="/",
    )


@router.post(
    "/register",
    response_model=AuthenticatedUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUserResponse:
    try:
        authenticated = await service.register(payload)
    except IdentityConflictError as error:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="identity_conflict",
            title="Account already exists",
            detail="An account already exists for this email address.",
        ) from error
    _set_session_cookie(response, request, authenticated.secret)
    response.headers["Location"] = "/api/v1/auth/me"
    return authenticated.user


@router.post("/login", response_model=AuthenticatedUserResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedUserResponse:
    try:
        authenticated = await service.login(payload)
    except InvalidCredentialsError as error:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
            title="Unable to sign in",
            detail="The email or password is incorrect.",
        ) from error
    _set_session_cookie(response, request, authenticated.secret)
    return authenticated.user


@router.get("/me", response_model=AuthenticatedUserResponse)
async def me(
    user: Annotated[AuthenticatedUserResponse, Depends(current_user)],
) -> AuthenticatedUserResponse:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    secret = request.cookies.get(request.app.state.settings.session_cookie_name)
    await service.logout(secret)
    response.delete_cookie(request.app.state.settings.session_cookie_name, path="/")
