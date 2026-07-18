"""Authorized Server-Sent Events chat endpoint."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.features.chat.dependencies import get_chat_service, require_actor
from app.features.chat.models import AuthenticatedActor
from app.features.chat.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ErrorEvent,
    ImageGenerationRequest,
    ImageGenerationResponse,
    encode_sse,
)
from app.features.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("/images", response_model=ImageGenerationResponse)
async def generate_business_image(
    payload: ImageGenerationRequest,
    actor: Annotated[AuthenticatedActor, Depends(require_actor)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ImageGenerationResponse:
    """Generate a visual only after an authenticated, explicit user request."""
    try:
        image_data_url = await service.generate_image(actor=actor, prompt=payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image generation is unavailable right now. Please retry later.",
        ) from exc
    return ImageGenerationResponse(image_data_url=image_data_url)


@router.get("/conversations/{conversation_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: UUID,
    actor: Annotated[AuthenticatedActor, Depends(require_actor)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatHistoryResponse:
    """Return only the authenticated actor's visible persisted conversation."""
    return await service.history(actor=actor, conversation_id=conversation_id)


@router.delete(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_chat_history(
    conversation_id: UUID,
    actor: Annotated[AuthenticatedActor, Depends(require_actor)],
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> None:
    """Clear the authenticated actor's persisted messages for one conversation."""
    await service.clear(actor=actor, conversation_id=conversation_id)


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
                business_context=payload.business_context,
                advisor_mode=payload.advisor_mode,
                response_depth=payload.response_depth,
                correlation_id=correlation_id,
                is_disconnected=request.is_disconnected,
            ):
                yield encode_sse(event)
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception(
                "chat_stream_failed",
                extra={
                    "conversation_id": str(conversation_id),
                    "correlation_id": str(correlation_id),
                },
            )
            yield encode_sse(ErrorEvent())

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
