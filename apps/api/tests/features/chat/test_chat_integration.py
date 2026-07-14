"""HTTP integration tests for authorized SSE chat."""

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agents.chat.graph import ChatGraphRunner
from app.agents.chat.state import ChatGraphState
from app.core.config import Settings
from app.features.chat.dependencies import get_chat_service, require_actor
from app.features.chat.models import AuthenticatedActor, MessageRole
from app.features.chat.repository import InMemoryMessageRepository
from app.features.chat.service import ChatService
from app.main import create_app

ACTOR = AuthenticatedActor(
    actor_id=UUID("20000000-0000-0000-0000-000000000001"),
    tenant_id=UUID("30000000-0000-0000-0000-000000000001"),
)
CONVERSATION_ID = UUID("10000000-0000-0000-0000-000000000001")
TEST_ENCRYPTION_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def _app() -> FastAPI:
    return create_app(
        Settings(
            environment="test",
            log_level="CRITICAL",
            database_url="sqlite+aiosqlite://",
            data_encryption_key=TEST_ENCRYPTION_KEY,
            session_cookie_secure=False,
        )
    )


@contextmanager
def _authenticated_client(app: FastAPI) -> Iterator[TestClient]:
    async def actor_override() -> AuthenticatedActor:
        return ACTOR

    app.dependency_overrides[require_actor] = actor_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_authorized_chat_streams_sse_and_persists_messages() -> None:
    app = _app()
    with _authenticated_client(app) as client:
        with client.stream(
            "POST",
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages",
            json={
                "message": "Explain this synthetic chat demonstration.",
                "advisor_mode": "scheme_navigator",
                "response_depth": "deep",
            },
        ) as response:
            body = response.read().decode()

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: status" in body
        assert "event: text_delta" in body
        assert "event: citation_preview" in body
        assert "synthetic-citation-001" in body
        assert "event: final" in body

        repository: InMemoryMessageRepository = app.state.chat_repository
        messages = asyncio.run(
            repository.list_for_conversation(
                tenant_id=ACTOR.tenant_id,
                actor_id=ACTOR.actor_id,
                conversation_id=CONVERSATION_ID,
            )
        )
        assert [message.role for message in messages] == [MessageRole.USER, MessageRole.ASSISTANT]

        history = client.get(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages"
        )
        assert history.status_code == 200
        assert [item["role"] for item in history.json()["items"]] == ["user", "assistant"]

        cleared = client.delete(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages"
        )
        assert cleared.status_code == 204
        empty_history = client.get(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages"
        )
        assert empty_history.json()["items"] == []


@pytest.mark.integration
def test_unauthorized_chat_is_rejected() -> None:
    with TestClient(_app()) as client:
        response = client.post(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages",
            json={"message": "This request has no trusted actor."},
        )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "authentication_required"


@pytest.mark.integration
def test_unknown_advisor_mode_is_rejected() -> None:
    app = _app()
    with _authenticated_client(app) as client:
        response = client.post(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages",
            json={"message": "Use an unsupported mode.", "advisor_mode": "unbounded_prompt"},
        )

    assert response.status_code == 422


@pytest.mark.integration
def test_provider_failure_returns_safe_terminal_sse_error() -> None:
    class FailingGraph(ChatGraphRunner):
        async def run(self, state: ChatGraphState) -> ChatGraphState:
            del state
            raise RuntimeError("synthetic provider secret must not escape")

    app = _app()
    service = ChatService(
        graph=FailingGraph.__new__(FailingGraph),
        repository=InMemoryMessageRepository(),
    )
    app.dependency_overrides[get_chat_service] = lambda: service
    with _authenticated_client(app) as client:
        response = client.post(
            f"/api/v1/chat/conversations/{CONVERSATION_ID}/messages",
            json={"message": "Trigger a synthetic provider failure."},
        )

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "answer_generation_failed" in response.text
    assert "synthetic provider secret" not in response.text
