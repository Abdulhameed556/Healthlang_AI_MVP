"""Persist and load chat sessions via backend repositories."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ai.src.application.chat.history import (
    TICKET_CREATED_METADATA_KEY,
    conversation_logs_to_message_history,
)
from ai.src.application.chat.pending_close import apply_pending_close_transition
from ai.src.application.chat.session_close import close_reason_for_state
from ai.src.domain.llm.messages import ChatMessage
from backend.src.domain.chat_sessions.entities import ChatSession, ConversationLog
from backend.src.domain.chat_sessions.value_objects import (
    ChatSessionConversationState,
    ChatSessionStatus,
    ConversationLogSpeaker,
)
from backend.src.infrastructure.database.session import async_session_factory
from backend.src.infrastructure.repositories.chat_sessions import SqlAlchemyChatSessionRepository
from backend.src.infrastructure.repositories.conversation_logs import (
    SqlAlchemyConversationLogRepository,
)
from backend.src.core.logging import green

logger = logging.getLogger(__name__)


class ChatSessionNotFoundError(Exception):
    """Raised when a session id does not exist."""


class ChatSessionClosedError(Exception):
    """Raised when a turn is attempted on an already-closed session."""

    def __init__(
        self,
        *,
        session_id: str,
        closed_at: datetime | None,
        close_reason: str | None,
    ) -> None:
        self.session_id = session_id
        self.closed_at = closed_at
        self.close_reason = close_reason
        super().__init__(
            "This conversation has ended. Please start a new session to continue."
        )


@dataclass(frozen=True)
class LoadedChatSession:
    session: ChatSession
    message_history: tuple[ChatMessage, ...]


class ChatSessionDbStore:
    """Load session state and append conversation turns to Postgres."""

    async def load(self, session_id: UUID) -> LoadedChatSession:
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            log_repo = SqlAlchemyConversationLogRepository(db)
            chat_session = await session_repo.find_by_id(session_id)
            if chat_session is None:
                raise ChatSessionNotFoundError(f"Chat session not found: {session_id}")
            logs = await log_repo.list_by_chat_session_id(session_id)
            return LoadedChatSession(
                session=chat_session,
                message_history=conversation_logs_to_message_history(logs),
            )

    async def find_active_by_freshchat_conversation(
        self,
        organization_id: UUID,
        conversation_id: str,
    ) -> ChatSession | None:
        """Return the active session for a Freshchat conversation, if any."""
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            return await session_repo.find_active_by_freshchat_conversation(
                organization_id, conversation_id
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
        chat_session: ChatSession | None = None,
        next_sequence_index: int | None = None,
    ) -> tuple[ConversationLog, ConversationLog]:
        """Append a user/agent turn. Pass ``chat_session`` and ``next_sequence_index``
        when the caller already loaded the session (avoids extra SELECTs).
        """
        now = datetime.now(timezone.utc)
        started = time.perf_counter()
        reused_session = chat_session is not None
        reused_sequence = next_sequence_index is not None
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            log_repo = SqlAlchemyConversationLogRepository(db)

            t_load = time.perf_counter()
            if chat_session is None:
                chat_session = await session_repo.find_by_id(session_id)
                if chat_session is None:
                    raise ChatSessionNotFoundError(f"Chat session not found: {session_id}")
            elif chat_session.id != session_id:
                raise ChatSessionNotFoundError(f"Chat session not found: {session_id}")
            t_after_load = time.perf_counter()

            t_seq = time.perf_counter()
            if next_sequence_index is None:
                sequence_index = await log_repo.next_sequence_index(session_id)
            else:
                sequence_index = next_sequence_index
            t_after_seq = time.perf_counter()

            turn_id = str(uuid4())
            user_log = ConversationLog(
                id=uuid4(),
                chat_session_id=session_id,
                ticket_id=chat_session.ticket_id,
                speaker=ConversationLogSpeaker.USER.value,
                content=user_content,
                sequence_index=sequence_index,
                spoken_at=now,
                metadata={**user_metadata, "turn_id": turn_id},
            )
            agent_log = ConversationLog(
                id=uuid4(),
                chat_session_id=session_id,
                ticket_id=chat_session.ticket_id,
                speaker=ConversationLogSpeaker.AGENT.value,
                content=agent_content,
                sequence_index=sequence_index + 1,
                spoken_at=now,
                metadata={**agent_metadata, "turn_id": turn_id},
            )
            t_insert = time.perf_counter()
            saved = await log_repo.add_many([user_log, agent_log])
            t_after_insert = time.perf_counter()

            close_reason = close_reason_for_state(conversation_state)
            if close_reason is not None:
                status = ChatSessionStatus.CLOSED.value
                closed_at = chat_session.closed_at or now
                final_close_reason = chat_session.close_reason or close_reason
            else:
                status = chat_session.status
                closed_at = chat_session.closed_at
                final_close_reason = chat_session.close_reason

            updated = ChatSession(
                id=chat_session.id,
                organization_id=chat_session.organization_id,
                agent_id=chat_session.agent_id,
                agent_version_id=chat_session.agent_version_id,
                widget_id=chat_session.widget_id,
                ticket_id=chat_session.ticket_id,
                status=status,
                conversation_state=conversation_state,
                close_reason=final_close_reason,
                metadata=session_metadata
                if session_metadata is not None
                else chat_session.metadata,
                started_at=chat_session.started_at,
                closed_at=closed_at,
                created_at=chat_session.created_at,
                updated_at=now,
            )
            t_save = time.perf_counter()
            await session_repo.save(updated)
            t_after_save = time.perf_counter()
            await db.commit()
            t_after_commit = time.perf_counter()

            logger.info(
                green(
                    "persist_turn session=%s total=%.2fs | load=%.2fs seq=%.2fs "
                    "insert=%.2fs save=%.2fs commit=%.2fs reused_session=%s"
                ),
                session_id,
                t_after_commit - started,
                t_after_load - t_load,
                t_after_seq - t_seq,
                t_after_insert - t_insert,
                t_after_save - t_save,
                t_after_commit - t_after_save,
                reused_session and reused_sequence,
            )
            return saved[0], saved[1]

    async def close_session(
        self,
        session_id: UUID,
        *,
        close_reason: str,
        conversation_state: str = ChatSessionConversationState.END_CONVERSATION.value,
    ) -> ChatSession:
        """Close a session directly (no conversation turn).

        Used by the grace-timeout worker. Idempotent: if the session is already
        closed it is returned unchanged. Clears the pending-close stamps.
        """
        now = datetime.now(timezone.utc)
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            chat_session = await session_repo.find_by_id(session_id)
            if chat_session is None:
                raise ChatSessionNotFoundError(f"Chat session not found: {session_id}")

            if chat_session.status != ChatSessionStatus.ACTIVE.value:
                return chat_session

            metadata = apply_pending_close_transition(
                chat_session.metadata,
                previous_state=chat_session.conversation_state,
                new_state=conversation_state,
            )
            updated = ChatSession(
                id=chat_session.id,
                organization_id=chat_session.organization_id,
                agent_id=chat_session.agent_id,
                agent_version_id=chat_session.agent_version_id,
                widget_id=chat_session.widget_id,
                ticket_id=chat_session.ticket_id,
                status=ChatSessionStatus.CLOSED.value,
                conversation_state=conversation_state,
                close_reason=close_reason,
                metadata=metadata,
                started_at=chat_session.started_at,
                closed_at=now,
                created_at=chat_session.created_at,
                updated_at=now,
            )
            await session_repo.save(updated)
            await db.commit()
            return updated

    async def update_metadata(
        self,
        session_id: UUID,
        metadata: dict,
        *,
        now: datetime | None = None,
    ) -> ChatSession:
        """Replace a session's metadata (read-modify-write done by the caller).

        Used by the post-close pipeline to stamp completion markers without
        changing status or conversation state.
        """
        now = now or datetime.now(timezone.utc)
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            chat_session = await session_repo.find_by_id(session_id)
            if chat_session is None:
                raise ChatSessionNotFoundError(f"Chat session not found: {session_id}")

            updated = ChatSession(
                id=chat_session.id,
                organization_id=chat_session.organization_id,
                agent_id=chat_session.agent_id,
                agent_version_id=chat_session.agent_version_id,
                widget_id=chat_session.widget_id,
                ticket_id=chat_session.ticket_id,
                status=chat_session.status,
                conversation_state=chat_session.conversation_state,
                close_reason=chat_session.close_reason,
                metadata=metadata,
                started_at=chat_session.started_at,
                closed_at=chat_session.closed_at,
                created_at=chat_session.created_at,
                updated_at=now,
            )
            await session_repo.save(updated)
            await db.commit()
            return updated

    async def stamp_ticket_marker_on_latest_agent_log(
        self,
        session_id: UUID,
        *,
        ref: str,
        summary: str | None,
    ) -> bool:
        """Record a ticket marker on the session's most recent assistant turn.

        Surfaced inline in history (see ``history.TICKET_CREATED_METADATA_KEY``)
        so later turns see, in context, that this issue was already ticketed and
        the orchestrator does not open a duplicate. Returns ``False`` when there
        is no assistant turn yet to mark.
        """
        async with async_session_factory() as db:
            log_repo = SqlAlchemyConversationLogRepository(db)
            latest = await log_repo.get_latest_by_speaker(
                session_id, ConversationLogSpeaker.AGENT.value
            )
            if latest is None:
                return False
            metadata = dict(latest.metadata or {})
            metadata[TICKET_CREATED_METADATA_KEY] = {
                "ref": ref,
                "summary": summary or "",
            }
            await log_repo.update_metadata(latest.id, metadata)
            await db.commit()
            return True

    async def create(
        self,
        *,
        organization_id: UUID,
        agent_id: UUID,
        agent_version_id: UUID | None = None,
        widget_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> ChatSession:
        now = datetime.now(timezone.utc)
        chat_session = ChatSession(
            id=uuid4(),
            organization_id=organization_id,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            widget_id=widget_id,
            ticket_id=None,
            status=ChatSessionStatus.ACTIVE.value,
            conversation_state=ChatSessionConversationState.IN_PROGRESS.value,
            close_reason=None,
            metadata=metadata or {},
            started_at=now,
            closed_at=None,
            created_at=now,
            updated_at=now,
        )
        async with async_session_factory() as db:
            session_repo = SqlAlchemyChatSessionRepository(db)
            created = await session_repo.add(chat_session)
            await db.commit()
            return created
