"""Message persistence contract and process-local vertical-slice adapter."""

import asyncio
from collections import defaultdict
from typing import Protocol
from uuid import UUID

from app.features.chat.models import ChatMessage


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

