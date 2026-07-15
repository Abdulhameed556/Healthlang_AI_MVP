"""Endpoint: send chat message."""
from fastapi import APIRouter, Depends, HTTPException, status

from ai.src.application.chat.dependencies import get_chat_pipeline
from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.application.chat.settings import DEFAULT_CHAT_CONFIG
from ai.src.application.chat.types import ChatPipelineInput
from ai.src.infrastructure.chat_sessions.db_store import ChatSessionNotFoundError
from ai.src.presentation.api.v1.chat.schemas import (
    SendChatMessageRequest,
    SendChatMessageResponse,
)

router = APIRouter()


@router.post(
    "/messages",
    summary="Send chat message",
    description="Run one chat turn for an existing session and return the agent reply.",
    response_model=SendChatMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def send_message(
    body: SendChatMessageRequest,
    pipeline: ChatPipeline = Depends(get_chat_pipeline),
) -> SendChatMessageResponse:
    try:
        result = await pipeline.run(
            ChatPipelineInput(
                session_id=body.session_id,
                user_message=body.message.strip(),
                config=DEFAULT_CHAT_CONFIG,
            )
        )
    except ChatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SendChatMessageResponse(
        session_id=result.session_id,
        agent_id=result.agent_id,
        version_id=result.version_id,
        message=result.message,
        conversation_state=result.conversation_state,
        pipeline_stopped=result.pipeline_stopped,
        timing_ms=result.timing_ms,
        turn_metadata=result.turn_metadata,
    )
