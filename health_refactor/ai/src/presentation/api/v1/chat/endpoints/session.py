"""Endpoint: create chat session."""
from fastapi import APIRouter, Depends, HTTPException, status

from ai.src.application.chat.create_session import create_chat_session
from ai.src.application.chat.dependencies import get_chat_session_store
from ai.src.application.chat.settings import DEFAULT_CHAT_CONFIG
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from ai.src.presentation.api.v1.chat.schemas import (
    CreateChatSessionRequest,
    CreateChatSessionResponse,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.agents.exceptions import (
    AgentNotDeployedError,
    AgentNotFoundError,
    AgentVersionNotFoundError,
)

router = APIRouter()


@router.post(
    "/sessions",
    summary="Create chat session",
    description=(
        "Start a new test chat session for an agent. Load the deployed version by "
        "default, or pass config_source=draft or config_source=version with "
        "version_id to preview unpublished configuration."
    ),
    response_model=CreateChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    body: CreateChatSessionRequest,
    store: ChatSessionStore = Depends(get_chat_session_store),
) -> CreateChatSessionResponse:
    try:
        result = await create_chat_session(
            agent_id=body.agent_id,
            mode=body.mode,
            config_source=body.config_source,
            version_id=body.version_id,
            use_session_cache=DEFAULT_CHAT_CONFIG.use_session_cache,
            store=store,
        )
    except AgentNotDeployedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except (AgentNotFoundError, AgentVersionNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return CreateChatSessionResponse.model_validate(result)
