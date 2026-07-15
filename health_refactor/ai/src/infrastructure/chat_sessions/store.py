"""Chat session store with optional Redis cache."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from ai.src.application.chat.session_close import close_reason_for_state
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_sessions.db_store import (
    ChatSessionDbStore,
    LoadedChatSession,
)
from ai.src.infrastructure.session_cache.cache import ChatSessionRedisCache
from ai.src.infrastructure.session_cache.factory import build_chat_session_cache
from backend.src.domain.chat_sessions.entities import ChatSession, ConversationLog
from backend.src.domain.chat_sessions.value_objects import ChatSessionStatus


@dataclass(frozen=True)
class SessionLoadReport:
    """Where session state was loaded from."""

    source: str  # cache | database


def apply_turn_to_loaded_session(
    loaded: LoadedChatSession,
    *,
    user_content: str,
    agent_content: str,
    conversation_state: str,
    session_metadata: dict | None,
) -> LoadedChatSession:
    """Update an in-memory session snapshot after a turn — avoids reloading all logs."""
    now = datetime.now(timezone.utc)
    session = loaded.session
    close_reason = close_reason_for_state(conversation_state)
    if close_reason is not None:
        status = ChatSessionStatus.CLOSED.value
        closed_at = session.closed_at or now
        final_close_reason = session.close_reason or close_reason
    else:
        status = session.status
        closed_at = session.closed_at
        final_close_reason = session.close_reason
    updated_session = ChatSession(
        id=session.id,
        organization_id=session.organization_id,
        agent_id=session.agent_id,
        agent_version_id=session.agent_version_id,
        widget_id=session.widget_id,
        ticket_id=session.ticket_id,
        status=status,
        conversation_state=conversation_state,
        close_reason=final_close_reason,
        metadata=session_metadata if session_metadata is not None else session.metadata,
        started_at=session.started_at,
        closed_at=closed_at,
        created_at=session.created_at,
        updated_at=now,
    )
    message_history = loaded.message_history + (
        ChatMessage(role=MessageRole.USER, content=user_content),
        ChatMessage(role=MessageRole.ASSISTANT, content=agent_content),
    )
    return LoadedChatSession(session=updated_session, message_history=message_history)


class ChatSessionStore:
    """Load and persist chat sessions with optional Redis write-through cache."""

    def __init__(
        self,
        *,
        db_store: ChatSessionDbStore | None = None,
        cache: ChatSessionRedisCache | None = None,
    ) -> None:
        self._db = db_store or ChatSessionDbStore()
        self._cache = cache or build_chat_session_cache()

    async def load(
        self,
        session_id: UUID,
        *,
        use_cache: bool = False,
    ) -> tuple[LoadedChatSession, SessionLoadReport]:
        if use_cache:
            cached = await self._cache.get(session_id)
            if cached is not None:
                return cached, SessionLoadReport(source="cache")

        loaded = await self._db.load(session_id)
        if use_cache:
            await self._cache.set(session_id, loaded)
        return loaded, SessionLoadReport(source="database")

    async def find_active_by_freshchat_conversation(
        self,
        organization_id: UUID,
        conversation_id: str,
    ) -> ChatSession | None:
        """Resolve the active session for a Freshchat conversation (DB-backed)."""
        return await self._db.find_active_by_freshchat_conversation(
            organization_id, conversation_id
        )

    async def append_turn_to_database(
        self,
        *,
        session_id: UUID,
        user_content: str,
        agent_content: str,
        conversation_state: str,
        user_metadata: dict,
        agent_metadata: dict,
        session_metadata: dict | None = None,
        chat_session: ChatSession | None = None,
        next_sequence_index: int | None = None,
    ) -> tuple[ConversationLog, ConversationLog]:
        """Persist a turn to Postgres only (no cache refresh)."""
        return await self._db.append_turn(
            session_id=session_id,
            user_content=user_content,
            agent_content=agent_content,
            conversation_state=conversation_state,
            user_metadata=user_metadata,
            agent_metadata=agent_metadata,
            session_metadata=session_metadata,
            chat_session=chat_session,
            next_sequence_index=next_sequence_index,
        )

    async def warm_cache_for_turn(
        self,
        *,
        session_id: UUID,
        user_content: str,
        agent_content: str,
        conversation_state: str,
        session_metadata: dict | None = None,
        cached_loaded: LoadedChatSession | None = None,
    ) -> None:
        """Optimistically update Redis before a deferred database write completes."""
        await self._refresh_cache_after_append(
            session_id=session_id,
            cached_loaded=cached_loaded,
            user_content=user_content,
            agent_content=agent_content,
            conversation_state=conversation_state,
            session_metadata=session_metadata,
        )

    async def append_turn(
        self,
        *,
        session_id: UUID,
        user_content: str,
        agent_content: str,
        conversation_state: str,
        user_metadata: dict,
        agent_metadata: dict,
        session_metadata: dict | None = None,
        cached_loaded: LoadedChatSession | None = None,
        use_cache: bool = False,
        chat_session: ChatSession | None = None,
        next_sequence_index: int | None = None,
    ) -> tuple[ConversationLog, ConversationLog]:
        saved = await self.append_turn_to_database(
            session_id=session_id,
            user_content=user_content,
            agent_content=agent_content,
            conversation_state=conversation_state,
            user_metadata=user_metadata,
            agent_metadata=agent_metadata,
            session_metadata=session_metadata,
            chat_session=chat_session,
            next_sequence_index=next_sequence_index,
        )
        if use_cache:
            await self._refresh_cache_after_append(
                session_id=session_id,
                cached_loaded=cached_loaded,
                user_content=user_content,
                agent_content=agent_content,
                conversation_state=conversation_state,
                session_metadata=session_metadata,
            )
        return saved

    async def _refresh_cache_after_append(
        self,
        *,
        session_id: UUID,
        cached_loaded: LoadedChatSession | None,
        user_content: str,
        agent_content: str,
        conversation_state: str,
        session_metadata: dict | None,
    ) -> None:
        base = cached_loaded
        if base is None:
            base = await self._cache.get(session_id)
        if base is not None:
            updated = apply_turn_to_loaded_session(
                base,
                user_content=user_content,
                agent_content=agent_content,
                conversation_state=conversation_state,
                session_metadata=session_metadata,
            )
            await self._cache.set(session_id, updated)
            return

        loaded = await self._db.load(session_id)
        await self._cache.set(session_id, loaded)

    async def create(
        self,
        *,
        organization_id: UUID,
        agent_id: UUID,
        agent_version_id: UUID | None = None,
        widget_id: UUID | None = None,
        metadata: dict | None = None,
        use_cache: bool = False,
    ) -> ChatSession:
        created = await self._db.create(
            organization_id=organization_id,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            widget_id=widget_id,
            metadata=metadata,
        )
        if use_cache:
            await self._cache.set(
                created.id,
                LoadedChatSession(session=created, message_history=()),
            )
        return created

    async def close_session(
        self,
        session_id: UUID,
        *,
        close_reason: str,
    ) -> ChatSession:
        """Close a session directly (grace-timeout path) and drop any cached copy."""
        closed = await self._db.close_session(session_id, close_reason=close_reason)
        await self._cache.invalidate(session_id)
        return closed

    async def update_metadata(
        self,
        session_id: UUID,
        metadata: dict,
    ) -> ChatSession:
        """Replace session metadata in Postgres and drop any cached copy."""
        updated = await self._db.update_metadata(session_id, metadata)
        await self._cache.invalidate(session_id)
        return updated

    async def stamp_ticket_marker_on_latest_agent_log(
        self,
        session_id: UUID,
        *,
        ref: str,
        summary: str | None,
    ) -> bool:
        """Mark the latest assistant turn as having opened a ticket; clears cache."""
        stamped = await self._db.stamp_ticket_marker_on_latest_agent_log(
            session_id, ref=ref, summary=summary
        )
        await self._cache.invalidate(session_id)
        return stamped

    async def invalidate_cache(self, session_id: UUID) -> int:
        return await self._cache.invalidate(session_id)
