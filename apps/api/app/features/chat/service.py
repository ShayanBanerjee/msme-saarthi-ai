"""Authorized chat use case and streaming persistence lifecycle."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.chat.citation_validation import validate_claim_citations
from app.agents.chat.graph import ChatGraphRunner
from app.agents.chat.image_provider import ImageGenerationProvider, OpenAIImageGenerationProvider
from app.agents.chat.provider import (
    DeterministicMockProvider,
    LLMProvider,
    OpenAIResponsesProvider,
    ProviderTimeoutError,
)
from app.agents.chat.retrieval import CuratedOfficialRetriever, MockRetriever, Retriever
from app.agents.chat.state import (
    AdvisorMode,
    BusinessContext,
    ChatGraphState,
    ConversationMessage,
    ResponseDepth,
    RetrievedEvidence,
)
from app.core.config import Settings
from app.features.chat.models import AuthenticatedActor, ChatMessage, MessageRole
from app.features.chat.repository import (
    InMemoryMessageRepository,
    MessageRepository,
    SqlAlchemyMessageRepository,
)
from app.features.chat.schemas import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatStreamEvent,
    CitationPreviewEvent,
    FinalEvent,
    StatusEvent,
    TextDeltaEvent,
    TextReplaceEvent,
)

type DisconnectCheck = Callable[[], Awaitable[bool]]


def _safe_fallback(
    evidence: tuple[RetrievedEvidence, ...], business_context: BusinessContext
) -> str:
    official = tuple(
        item
        for item in evidence
        if getattr(getattr(item, "citation", None), "source_kind", None) == "official_scheme"
    )
    if not official:
        confirmed = ", ".join(
            part
            for part in (
                f"stage: {business_context.stage.value}" if business_context.stage else None,
                f"location: {business_context.location}" if business_context.location else None,
                f"sector: {business_context.sector}" if business_context.sector else None,
                f"priority: {business_context.goal.value}" if business_context.goal else None,
            )
            if part
        )
        if confirmed:
            return (
                "I understood the confirmed business brief ("
                f"{confirmed}), but I could not validate a scheme-specific answer from the "
                "current evidence. Please add the exact amount or outcome you need, its timing, "
                "and the expense it will cover so I can search again. I have not made an "
                "eligibility or approval decision."
            )
        return (
            "I could not complete a fully validated answer from current evidence. Please share "
            "your State or Union Territory, sector, business stage, and funding or growth need "
            "so I can search again."
        )
    sources = "\n".join(
        f"- Review {item.citation.source_label} [{item.citation.citation_id}]"
        for item in official
    )
    return (
        "I could not complete a fully validated generated answer. These reviewed official "
        f"sources are the safest next references:\n{sources}\n"
        "Please verify current terms with the linked authority. I have not made an eligibility "
        "or approval decision."
    )


class ChatService:
    """Persist a user message, run the graph, stream, then persist the assistant message."""

    def __init__(
        self,
        *,
        graph: ChatGraphRunner,
        repository: MessageRepository,
        prompt_version: str = "chat.synthetic.v1",
        generation_timeout_seconds: float = 30.0,
        image_provider: ImageGenerationProvider | None = None,
    ) -> None:
        self._graph = graph
        self._repository = repository
        self._prompt_version = prompt_version
        self._generation_timeout_seconds = generation_timeout_seconds
        self._image_provider = image_provider

    async def generate_image(self, *, actor: AuthenticatedActor, prompt: str) -> str:
        """Generate an explicitly requested visual without persisting it as scheme evidence."""
        del actor
        if self._image_provider is None:
            raise RuntimeError("image generation is not configured")
        return await self._image_provider.generate(prompt)

    async def stream_message(
        self,
        *,
        actor: AuthenticatedActor,
        conversation_id: UUID,
        message: str,
        business_context: BusinessContext,
        correlation_id: UUID,
        is_disconnected: DisconnectCheck,
        advisor_mode: AdvisorMode = AdvisorMode.BUSINESS_ANALYST,
        response_depth: ResponseDepth = ResponseDepth.BALANCED,
    ) -> AsyncIterator[ChatStreamEvent]:
        history = await self._repository.list_for_conversation(
            tenant_id=actor.tenant_id,
            actor_id=actor.actor_id,
            conversation_id=conversation_id,
        )
        visible_history = tuple(
            ConversationMessage(role=item.role.value, content=item.content)
            for item in history[-12:]
        )
        user_message = ChatMessage(
            conversation_id=conversation_id,
            actor_id=actor.actor_id,
            tenant_id=actor.tenant_id,
            role=MessageRole.USER,
            content=message,
        )
        await self._repository.add(user_message)
        yield StatusEvent(status="understanding")
        if await is_disconnected():
            return
        yield StatusEvent(status="retrieving")
        if await is_disconnected():
            return

        result = await self._graph.prepare(
            ChatGraphState(
                conversation_id=conversation_id,
                actor_id=actor.actor_id,
                tenant_id=actor.tenant_id,
                correlation_id=correlation_id,
                user_message=message,
                business_context=business_context,
                advisor_mode=advisor_mode,
                response_depth=response_depth,
                conversation=visible_history,
                prompt_version=self._prompt_version,
            )
        )
        yield StatusEvent(status="generating")
        for evidence in result.evidence:
            if await is_disconnected():
                return
            yield CitationPreviewEvent(citation=evidence.citation)

        chunks: list[str] = []
        fallback_reason: Literal["provider_timeout", "citation_validation_failed"] | None = None
        try:
            async with asyncio.timeout(self._generation_timeout_seconds):
                stream = self._graph.stream_answer(result)
                pending: list[str] = []
                pending_length = 0
                try:
                    async for chunk in stream:
                        if await is_disconnected():
                            return
                        chunks.append(chunk)
                        pending.append(chunk)
                        pending_length += len(chunk)
                        if (
                            pending_length >= 180
                            or "\n" in chunk
                        ):
                            yield TextDeltaEvent(text="".join(pending))
                            pending = []
                            pending_length = 0
                    if pending:
                        yield TextDeltaEvent(text="".join(pending))
                finally:
                    await stream.aclose()
        except (TimeoutError, ProviderTimeoutError):
            fallback_reason = "provider_timeout"

        answer = "".join(chunks).strip()
        validation = validate_claim_citations(answer, result.evidence) if answer else None
        if fallback_reason is None and (validation is None or not validation.valid):
            fallback_reason = "citation_validation_failed"
        if fallback_reason is not None:
            answer = _safe_fallback(result.evidence, business_context)
            yield TextReplaceEvent(text=answer)
            citation_ids = tuple(
                item.citation.citation_id
                for item in result.evidence
                if item.citation.source_kind == "official_scheme"
            )
        else:
            assert validation is not None
            citation_ids = validation.cited_ids

        if await is_disconnected():
            return
        assistant_message = ChatMessage(
            conversation_id=conversation_id,
            actor_id=actor.actor_id,
            tenant_id=actor.tenant_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citation_ids=citation_ids,
        )
        await self._repository.add(assistant_message)
        yield FinalEvent(
            message_id=assistant_message.id,
            citations=tuple(
                item.citation
                for item in result.evidence
                if item.citation.citation_id in citation_ids
            ),
            prompt_version=result.prompt_version,
            completion_status="fallback" if fallback_reason else "validated",
            fallback_reason=fallback_reason,
        )

    async def history(
        self, *, actor: AuthenticatedActor, conversation_id: UUID
    ) -> ChatHistoryResponse:
        messages = await self._repository.list_for_conversation(
            tenant_id=actor.tenant_id,
            actor_id=actor.actor_id,
            conversation_id=conversation_id,
        )
        return ChatHistoryResponse(
            conversation_id=conversation_id,
            items=tuple(
                ChatHistoryItem(
                    role=item.role,
                    content=item.content,
                    citation_ids=item.citation_ids,
                )
                for item in messages
            ),
        )

    async def clear(self, *, actor: AuthenticatedActor, conversation_id: UUID) -> None:
        """Clear only the authenticated actor's current conversation."""
        await self._repository.delete_conversation(
            tenant_id=actor.tenant_id,
            actor_id=actor.actor_id,
            conversation_id=conversation_id,
        )


def create_default_chat_service(
    *,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession] | None,
    retriever_override: Retriever | None = None,
) -> tuple[ChatService, MessageRepository]:
    """Select explicit local/production adapters from validated configuration."""
    repository: MessageRepository = (
        InMemoryMessageRepository()
        if session_factory is None or settings.environment == "test"
        else SqlAlchemyMessageRepository(session_factory)
    )
    retriever: Retriever = retriever_override or (
        MockRetriever() if settings.environment == "test" else CuratedOfficialRetriever()
    )
    provider: LLMProvider = DeterministicMockProvider()
    image_provider: ImageGenerationProvider | None = None
    if settings.environment != "test" and settings.llm_provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("MSME_SAARTHI_OPENAI_API_KEY is required when llm_provider=openai")
        provider = OpenAIResponsesProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            base_url=settings.openai_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        image_provider = OpenAIImageGenerationProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_image_model,
            base_url=settings.openai_base_url,
            timeout_seconds=settings.image_generation_timeout_seconds,
        )
    graph = ChatGraphRunner(retriever=retriever, provider=provider)
    return ChatService(
        graph=graph,
        repository=repository,
        prompt_version="chat.advisor.v4",
        generation_timeout_seconds=settings.llm_timeout_seconds,
        image_provider=image_provider,
    ), repository
