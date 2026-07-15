"""Load real customer conversations from DB for conversation eval."""
import logging
from uuid import UUID

from sqlalchemy import or_, select

from ai.src.application.chat_evaluation.context import ChatEvalContext
from backend.src.domain.chat_sessions.value_objects import CHAT_SESSION_MODE_TEST
from backend.src.infrastructure.database.models.chat_session import (
    ChatSession as ChatSessionModel,
)
from backend.src.infrastructure.database.models.conversation_log import (
    ConversationLog as ConversationLogModel,
)
from backend.src.infrastructure.database.session import async_session_factory

_log = logging.getLogger(__name__)

_DEFAULT_SAMPLE = 10


class LoadRealConversationsStep:
    """Populate ctx.conversations from stored chat_sessions + logs."""

    async def run(self, ctx: ChatEvalContext) -> None:
        agent_id = ctx.agent_id
        if not agent_id:
            raise ValueError(
                "agent_id is required for conversation evaluation"
            )
        sample_size = getattr(ctx, "sample_size", _DEFAULT_SAMPLE)
        agent_uuid = UUID(agent_id)

        async with async_session_factory() as db:
            mode_path = ChatSessionModel.metadata_["mode"].astext
            sessions = (
                await db.execute(
                    select(ChatSessionModel)
                    .where(
                        ChatSessionModel.agent_id == agent_uuid,
                        or_(mode_path.is_(None), mode_path != CHAT_SESSION_MODE_TEST),
                    )
                    .order_by(ChatSessionModel.started_at.desc())
                    .limit(sample_size)
                )
            ).scalars().all()

            if not sessions:
                _log.warning(
                    "load_real_conversations agent=%s found 0 sessions",
                    agent_id,
                )
                return

            for chat_session in sessions:
                logs = (
                    await db.execute(
                        select(ConversationLogModel)
                        .where(
                            ConversationLogModel.chat_session_id
                            == chat_session.id
                        )
                        .order_by(
                            ConversationLogModel.sequence_index.asc()
                        )
                    )
                ).scalars().all()

                user_turns = [
                    {"user": log.content, "agent_expected": ""}
                    for log in logs
                    if log.speaker == "user"
                ]
                if not user_turns:
                    continue

                ctx.conversations.append(
                    {
                        "scenario_id": str(chat_session.id),
                        "scenario_name": (
                            f"Session {str(chat_session.id)[:8]}"
                        ),
                        "persona": "real_customer",
                        "turns": user_turns,
                    }
                )

        _log.info(
            "load_real_conversations agent=%s loaded=%d sessions",
            agent_id,
            len(ctx.conversations),
        )
