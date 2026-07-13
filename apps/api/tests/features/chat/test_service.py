"""Chat streaming lifecycle tests."""

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from app.agents.chat.graph import ChatGraphRunner
from app.agents.chat.provider import DeterministicMockProvider
from app.agents.chat.retrieval import MockRetriever
from app.features.chat.models import AuthenticatedActor, MessageRole
from app.features.chat.repository import InMemoryMessageRepository
from app.features.chat.schemas import ChatStreamEvent, FinalEvent, StatusEvent
from app.features.chat.service import ChatService

ACTOR = AuthenticatedActor(
    actor_id=UUID("20000000-0000-0000-0000-000000000001"),
    tenant_id=UUID("30000000-0000-0000-0000-000000000001"),
)
CONVERSATION_ID = UUID("10000000-0000-0000-0000-000000000001")
CORRELATION_ID = UUID("40000000-0000-0000-0000-000000000001")


def _service() -> tuple[ChatService, InMemoryMessageRepository, DeterministicMockProvider]:
    provider = DeterministicMockProvider()
    repository = InMemoryMessageRepository()
    graph = ChatGraphRunner(retriever=MockRetriever(), provider=provider)
    return ChatService(graph=graph, repository=repository), repository, provider


async def _collect(stream: AsyncIterator[ChatStreamEvent]) -> tuple[ChatStreamEvent, ...]:
    return tuple([event async for event in stream])


async def _connected() -> bool:
    return False


async def _disconnected() -> bool:
    return True


def test_completed_stream_persists_user_and_assistant_messages() -> None:
    async def scenario() -> None:
        service, repository, provider = _service()
        events = await _collect(
            service.stream_message(
                actor=ACTOR,
                conversation_id=CONVERSATION_ID,
                message="Tell me about the synthetic source.",
                correlation_id=CORRELATION_ID,
                is_disconnected=_connected,
            )
        )
        messages = await repository.list_for_conversation(
            tenant_id=ACTOR.tenant_id,
            actor_id=ACTOR.actor_id,
            conversation_id=CONVERSATION_ID,
        )

        assert isinstance(events[0], StatusEvent)
        assert isinstance(events[-1], FinalEvent)
        assert [message.role for message in messages] == [MessageRole.USER, MessageRole.ASSISTANT]
        assert messages[-1].citation_ids == ("synthetic-citation-001",)
        assert len(provider.calls) == 1

    asyncio.run(scenario())


def test_disconnect_stops_graph_and_does_not_persist_assistant() -> None:
    async def scenario() -> None:
        service, repository, provider = _service()
        events = await _collect(
            service.stream_message(
                actor=ACTOR,
                conversation_id=CONVERSATION_ID,
                message="Disconnect this synthetic request.",
                correlation_id=CORRELATION_ID,
                is_disconnected=_disconnected,
            )
        )
        messages = await repository.list_for_conversation(
            tenant_id=ACTOR.tenant_id,
            actor_id=ACTOR.actor_id,
            conversation_id=CONVERSATION_ID,
        )

        assert events == (StatusEvent(status="retrieving"),)
        assert [message.role for message in messages] == [MessageRole.USER]
        assert provider.calls == []

    asyncio.run(scenario())

