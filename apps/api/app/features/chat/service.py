"""Authorized chat use case and streaming persistence lifecycle."""

from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID

from app.agents.chat.graph import ChatGraphRunner
from app.agents.chat.provider import DeterministicMockProvider
from app.agents.chat.retrieval import MockRetriever
from app.agents.chat.state import ChatGraphState
from app.features.chat.models import AuthenticatedActor, ChatMessage, MessageRole
from app.features.chat.repository import InMemoryMessageRepository, MessageRepository
from app.features.chat.schemas import (
    ChatStreamEvent,
    CitationPreviewEvent,
    FinalEvent,
    StatusEvent,
    TextDeltaEvent,
)

type DisconnectCheck = Callable[[], Awaitable[bool]]


def _text_chunks(text: str, words_per_chunk: int = 6) -> tuple[str, ...]:
    words = text.split()
    return tuple(
        " ".join(words[index : index + words_per_chunk])
        + (" " if index + words_per_chunk < len(words) else "")
        for index in range(0, len(words), words_per_chunk)
    )


class ChatService:
    """Persist a user message, run the graph, stream, then persist the assistant message."""

    def __init__(self, *, graph: ChatGraphRunner, repository: MessageRepository) -> None:
        self._graph = graph
        self._repository = repository

    async def stream_message(
        self,
        *,
        actor: AuthenticatedActor,
        conversation_id: UUID,
        message: str,
        correlation_id: UUID,
        is_disconnected: DisconnectCheck,
    ) -> AsyncIterator[ChatStreamEvent]:
        user_message = ChatMessage(
            conversation_id=conversation_id,
            actor_id=actor.actor_id,
            tenant_id=actor.tenant_id,
            role=MessageRole.USER,
            content=message,
        )
        await self._repository.add(user_message)
        yield StatusEvent(status="retrieving")
        if await is_disconnected():
            return

        result = await self._graph.run(
            ChatGraphState(
                conversation_id=conversation_id,
                actor_id=actor.actor_id,
                tenant_id=actor.tenant_id,
                correlation_id=correlation_id,
                user_message=message,
            )
        )
        yield StatusEvent(status="generating")
        for evidence in result.evidence:
            if await is_disconnected():
                return
            yield CitationPreviewEvent(citation=evidence.citation)

        if result.answer is None:
            raise RuntimeError("chat graph completed without an answer")
        for chunk in _text_chunks(result.answer):
            if await is_disconnected():
                return
            yield TextDeltaEvent(text=chunk)

        if await is_disconnected():
            return
        assistant_message = ChatMessage(
            conversation_id=conversation_id,
            actor_id=actor.actor_id,
            tenant_id=actor.tenant_id,
            role=MessageRole.ASSISTANT,
            content=result.answer,
            citation_ids=tuple(item.citation.citation_id for item in result.evidence),
        )
        await self._repository.add(assistant_message)
        yield FinalEvent(
            message_id=assistant_message.id,
            citations=tuple(item.citation for item in result.evidence),
            prompt_version=result.prompt_version,
        )


def create_default_chat_service() -> tuple[ChatService, InMemoryMessageRepository]:
    """Create the local synthetic slice; production auth remains fail-closed."""
    repository = InMemoryMessageRepository()
    graph = ChatGraphRunner(retriever=MockRetriever(), provider=DeterministicMockProvider())
    return ChatService(graph=graph, repository=repository), repository
