"""Tenant-scoped identity persistence boundary and SQLAlchemy adapter."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import Row, Select, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.auth.models import (
    AuthSessionRecord,
    EnterpriseProfileRecord,
    MembershipRecord,
    TenantRecord,
    UserRecord,
)


class DuplicateIdentityError(Exception):
    """Raised when a normalized identity already exists."""


@dataclass(frozen=True)
class StoredAccount:
    user_id: UUID
    tenant_id: UUID
    email_ciphertext: str
    password_hash: str
    full_name_ciphertext: str
    business_name_ciphertext: str


@dataclass(frozen=True)
class NewAccount:
    email_lookup: str
    email_ciphertext: str
    password_hash: str
    full_name_ciphertext: str
    business_name_ciphertext: str
    tenant_name_ciphertext: str


@dataclass(frozen=True)
class NewSession:
    user_id: UUID
    tenant_id: UUID
    token_hash: str
    idle_expires_at: datetime
    absolute_expires_at: datetime


class AuthRepository(Protocol):
    async def create_account(self, account: NewAccount) -> StoredAccount: ...
    async def get_account_by_email_lookup(self, email_lookup: str) -> StoredAccount | None: ...
    async def get_account_by_session_hash(
        self, token_hash: str, now: datetime
    ) -> StoredAccount | None: ...
    async def create_session(self, session: NewSession) -> None: ...
    async def touch_session(self, token_hash: str, last_seen_at: datetime) -> None: ...
    async def revoke_session(self, token_hash: str, revoked_at: datetime) -> None: ...


class SqlAlchemyAuthRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = session_factory

    async def create_account(self, account: NewAccount) -> StoredAccount:
        try:
            async with self._sessions.begin() as session:
                user = UserRecord(
                    email_lookup=account.email_lookup,
                    email_ciphertext=account.email_ciphertext,
                    password_hash=account.password_hash,
                )
                tenant = TenantRecord(name_ciphertext=account.tenant_name_ciphertext)
                session.add_all([user, tenant])
                await session.flush()
                session.add_all(
                    [
                        MembershipRecord(tenant_id=tenant.id, user_id=user.id, role="owner"),
                        EnterpriseProfileRecord(
                            tenant_id=tenant.id,
                            owner_user_id=user.id,
                            full_name_ciphertext=account.full_name_ciphertext,
                            business_name_ciphertext=account.business_name_ciphertext,
                        ),
                    ]
                )
                await session.flush()
                return StoredAccount(
                    user_id=user.id,
                    tenant_id=tenant.id,
                    email_ciphertext=user.email_ciphertext,
                    password_hash=user.password_hash,
                    full_name_ciphertext=account.full_name_ciphertext,
                    business_name_ciphertext=account.business_name_ciphertext,
                )
        except IntegrityError as error:
            raise DuplicateIdentityError from error

    async def get_account_by_email_lookup(self, email_lookup: str) -> StoredAccount | None:
        async with self._sessions() as session:
            statement = self._account_statement().where(UserRecord.email_lookup == email_lookup)
            return self._to_account((await session.execute(statement)).one_or_none())

    async def get_account_by_session_hash(
        self, token_hash: str, now: datetime
    ) -> StoredAccount | None:
        async with self._sessions() as session:
            statement = (
                self._account_statement()
                .join(
                    AuthSessionRecord,
                    (AuthSessionRecord.user_id == UserRecord.id)
                    & (AuthSessionRecord.tenant_id == MembershipRecord.tenant_id),
                )
                .where(
                    AuthSessionRecord.token_hash == token_hash,
                    AuthSessionRecord.revoked_at.is_(None),
                    AuthSessionRecord.idle_expires_at > now,
                    AuthSessionRecord.absolute_expires_at > now,
                    UserRecord.status == "active",
                    MembershipRecord.status == "active",
                )
            )
            return self._to_account((await session.execute(statement)).one_or_none())

    async def create_session(self, new_session: NewSession) -> None:
        async with self._sessions.begin() as session:
            session.add(
                AuthSessionRecord(
                    user_id=new_session.user_id,
                    tenant_id=new_session.tenant_id,
                    token_hash=new_session.token_hash,
                    idle_expires_at=new_session.idle_expires_at,
                    absolute_expires_at=new_session.absolute_expires_at,
                )
            )

    async def touch_session(self, token_hash: str, last_seen_at: datetime) -> None:
        async with self._sessions.begin() as session:
            await session.execute(
                update(AuthSessionRecord)
                .where(AuthSessionRecord.token_hash == token_hash)
                .values(last_seen_at=last_seen_at)
            )

    async def revoke_session(self, token_hash: str, revoked_at: datetime) -> None:
        async with self._sessions.begin() as session:
            await session.execute(
                update(AuthSessionRecord)
                .where(AuthSessionRecord.token_hash == token_hash)
                .values(revoked_at=revoked_at)
            )

    @staticmethod
    def _account_statement() -> Select[tuple[UUID, UUID, str, str, str, str]]:
        return (
            select(
                UserRecord.id,
                MembershipRecord.tenant_id,
                UserRecord.email_ciphertext,
                UserRecord.password_hash,
                EnterpriseProfileRecord.full_name_ciphertext,
                EnterpriseProfileRecord.business_name_ciphertext,
            )
            .join(MembershipRecord, MembershipRecord.user_id == UserRecord.id)
            .join(
                EnterpriseProfileRecord,
                (EnterpriseProfileRecord.owner_user_id == UserRecord.id)
                & (EnterpriseProfileRecord.tenant_id == MembershipRecord.tenant_id),
            )
        )

    @staticmethod
    def _to_account(
        row: Row[tuple[UUID, UUID, str, str, str, str]] | None,
    ) -> StoredAccount | None:
        if row is None:
            return None
        user_id, tenant_id, email, password, full_name, business_name = row
        return StoredAccount(
            user_id=user_id,
            tenant_id=tenant_id,
            email_ciphertext=email,
            password_hash=password,
            full_name_ciphertext=full_name,
            business_name_ciphertext=business_name,
        )
