"""Message persistence contract and process-local vertical-slice adapter."""

import asyncio
from collections import defaultdict
from typing import Protocol
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.chat.models import ChatMessage, ChatMessageRecord, MessageRole


class MessageRepository(Protocol):
    """Asynchronous storage boundary for chat messages."""

    async def add(self, message: ChatMessage) -> None:
        """Persist one immutable message."""
        ...

    async def list_for_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> tuple[ChatMessage, ...]:
        """List messages within the authorized tenant/actor boundary."""
        ...

    async def delete_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> None:
        """Delete messages only within the authorized tenant/actor boundary."""
        ...


class InMemoryMessageRepository:
    """Concurrency-safe process-local adapter to be replaced by PostgreSQL."""

    def __init__(self) -> None:
        self._messages: defaultdict[tuple[UUID, UUID, UUID], list[ChatMessage]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def add(self, message: ChatMessage) -> None:
        key = (message.tenant_id, message.actor_id, message.conversation_id)
        async with self._lock:
            self._messages[key].append(message)

    async def list_for_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> tuple[ChatMessage, ...]:
        key = (tenant_id, actor_id, conversation_id)
        async with self._lock:
            return tuple(self._messages[key])

    async def delete_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> None:
        key = (tenant_id, actor_id, conversation_id)
        async with self._lock:
            self._messages.pop(key, None)


class SqlAlchemyMessageRepository:
    """PostgreSQL/SQLAlchemy adapter enforcing tenant and actor filters."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, message: ChatMessage) -> None:
        async with self._session_factory() as session, session.begin():
            session.add(
                ChatMessageRecord(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    actor_id=message.actor_id,
                    tenant_id=message.tenant_id,
                    role=message.role.value,
                    content=message.content,
                    citation_ids=list(message.citation_ids),
                    created_at=message.created_at,
                )
            )

    async def list_for_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> tuple[ChatMessage, ...]:
        statement = (
            select(ChatMessageRecord)
            .where(
                ChatMessageRecord.tenant_id == tenant_id,
                ChatMessageRecord.actor_id == actor_id,
                ChatMessageRecord.conversation_id == conversation_id,
            )
            .order_by(ChatMessageRecord.created_at, ChatMessageRecord.id)
        )
        async with self._session_factory() as session:
            records = (await session.scalars(statement)).all()
        return tuple(
            ChatMessage(
                id=item.id,
                conversation_id=item.conversation_id,
                actor_id=item.actor_id,
                tenant_id=item.tenant_id,
                role=MessageRole(item.role),
                content=item.content,
                citation_ids=tuple(item.citation_ids),
                created_at=item.created_at,
            )
            for item in records
        )

    async def delete_conversation(
        self, *, tenant_id: UUID, actor_id: UUID, conversation_id: UUID
    ) -> None:
        statement = delete(ChatMessageRecord).where(
            ChatMessageRecord.tenant_id == tenant_id,
            ChatMessageRecord.actor_id == actor_id,
            ChatMessageRecord.conversation_id == conversation_id,
        )
        async with self._session_factory() as session, session.begin():
            await session.execute(statement)
