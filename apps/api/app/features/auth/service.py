"""Registration, credentials, secure-session, and identity use cases."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.features.auth.crypto import CredentialProtector, DataCipher
from app.features.auth.repository import (
    AuthRepository,
    DuplicateIdentityError,
    NewAccount,
    NewSession,
    StoredAccount,
)
from app.features.auth.schemas import AuthenticatedUserResponse, LoginRequest, RegisterRequest


class IdentityConflictError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedSession:
    secret: str
    user: AuthenticatedUserResponse


class AuthService:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        cipher: DataCipher,
        credentials: CredentialProtector,
        idle_minutes: int,
        absolute_hours: int,
    ) -> None:
        self._repository = repository
        self._cipher = cipher
        self._credentials = credentials
        self._idle_delta = timedelta(minutes=idle_minutes)
        self._absolute_delta = timedelta(hours=absolute_hours)

    async def register(self, request: RegisterRequest) -> AuthenticatedSession:
        email_lookup = self._cipher.blind_index(request.email, field="email_lookup")
        account = NewAccount(
            email_lookup=email_lookup,
            email_ciphertext=self._cipher.encrypt(request.email, field="email"),
            password_hash=self._credentials.hash_password(request.password),
            full_name_ciphertext=self._cipher.encrypt(request.full_name, field="full_name"),
            business_name_ciphertext=self._cipher.encrypt(
                request.business_name, field="business_name"
            ),
            tenant_name_ciphertext=self._cipher.encrypt(
                request.business_name, field="tenant_name"
            ),
        )
        try:
            stored = await self._repository.create_account(account)
        except DuplicateIdentityError as error:
            raise IdentityConflictError from error
        return await self._issue_session(stored)

    async def login(self, request: LoginRequest) -> AuthenticatedSession:
        email_lookup = self._cipher.blind_index(request.email, field="email_lookup")
        account = await self._repository.get_account_by_email_lookup(email_lookup)
        if not self._credentials.verify_password(
            account.password_hash if account else None, request.password
        ):
            raise InvalidCredentialsError
        if account is None:  # Defensive narrowing; valid credentials imply an account.
            raise InvalidCredentialsError
        return await self._issue_session(account)

    async def authenticate(self, secret: str | None) -> AuthenticatedUserResponse | None:
        if not secret:
            return None
        token_hash = self._credentials.hash_session_secret(secret)
        now = datetime.now(UTC)
        account = await self._repository.get_account_by_session_hash(token_hash, now)
        if account is None:
            return None
        await self._repository.touch_session(token_hash, now)
        return self._public_user(account)

    async def logout(self, secret: str | None) -> None:
        if not secret:
            return
        await self._repository.revoke_session(
            self._credentials.hash_session_secret(secret), datetime.now(UTC)
        )

    async def _issue_session(self, account: StoredAccount) -> AuthenticatedSession:
        secret = self._credentials.new_session_secret()
        now = datetime.now(UTC)
        await self._repository.create_session(
            NewSession(
                user_id=account.user_id,
                tenant_id=account.tenant_id,
                token_hash=self._credentials.hash_session_secret(secret),
                idle_expires_at=now + self._idle_delta,
                absolute_expires_at=now + self._absolute_delta,
            )
        )
        return AuthenticatedSession(secret=secret, user=self._public_user(account))

    def _public_user(self, account: StoredAccount) -> AuthenticatedUserResponse:
        full_name = self._cipher.decrypt(account.full_name_ciphertext, field="full_name")
        words = full_name.split()
        initials = "".join(word[0].upper() for word in words[:2])
        return AuthenticatedUserResponse(
            id=account.user_id,
            tenant_id=account.tenant_id,
            email=self._cipher.decrypt(account.email_ciphertext, field="email"),
            full_name=full_name,
            business_name=self._cipher.decrypt(
                account.business_name_ciphertext, field="business_name"
            ),
            initials=initials,
        )


def user_actor_ids(user: AuthenticatedUserResponse) -> tuple[UUID, UUID]:
    return user.id, user.tenant_id
