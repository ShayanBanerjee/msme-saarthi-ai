"""Minimal chat graph contract tests."""

import asyncio
from uuid import UUID

from app.agents.chat.graph import ChatGraphRunner
from app.agents.chat.provider import DeterministicMockProvider
from app.agents.chat.retrieval import MockRetriever
from app.agents.chat.state import BusinessContext, BusinessStage, ChatGraphState


def test_graph_retrieves_evidence_and_calls_provider() -> None:
    provider = DeterministicMockProvider()
    graph = ChatGraphRunner(retriever=MockRetriever(), provider=provider)
    state = ChatGraphState(
        conversation_id=UUID("10000000-0000-0000-0000-000000000001"),
        actor_id=UUID("20000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("30000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("40000000-0000-0000-0000-000000000001"),
        user_message="How does this synthetic demonstration work?",
        business_context=BusinessContext(stage=BusinessStage.IDEA),
    )

    result = asyncio.run(graph.run(state))

    assert result.answer is not None
    assert result.evidence[0].citation.citation_id == "synthetic-citation-001"
    assert len(provider.calls) == 1
    assert provider.calls[0].user_message == state.user_message
    assert provider.calls[0].prompt_version == "chat.synthetic.v1"
    assert provider.calls[0].business_context.stage == BusinessStage.IDEA
