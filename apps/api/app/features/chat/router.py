"""Authorized Server-Sent Events chat endpoint."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.features.chat.dependencies import get_chat_service, require_actor
from app.features.chat.models import AuthenticatedActor
from app.features.chat.schemas import ChatRequest, encode_sse
from app.features.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
)
async def stream_chat_message(
    conversation_id: UUID,
    payload: ChatRequest,
    request: Request,
    actor: Annotated[AuthenticatedActor, Depends(require_actor)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> StreamingResponse:
    """Stream provisional graph output and persist only a completed assistant message."""
    correlation_id = UUID(str(request.state.correlation_id))

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for event in service.stream_message(
                actor=actor,
                conversation_id=conversation_id,
                message=payload.message,
                correlation_id=correlation_id,
                is_disconnected=request.is_disconnected,
            ):
                yield encode_sse(event)
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
