from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.conversation_session import ConversationSession
from typing import Optional


class ChatService:
    async def list_sessions(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(ConversationSession).order_by(ConversationSession.started_at.desc())
        if client_phone:
            statement = statement.where(ConversationSession.client_phone == client_phone)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_session(self, session_id: str, session: AsyncSession):
        statement = select(ConversationSession).where(ConversationSession.session_id == session_id)
        result = await session.exec(statement)
        return result.first()

    async def log_interaction(
        self, 
        session: AsyncSession, 
        client_phone: str, 
        escalated: bool = False
    ):
        from datetime import datetime, timedelta
        # Find active session from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        statement = select(ConversationSession).where(
            ConversationSession.client_phone == client_phone,
            ConversationSession.started_at >= today_start
        ).order_by(ConversationSession.started_at.desc())
        
        result = await session.exec(statement)
        active_session = result.first()
        
        if not active_session:
            active_session = ConversationSession(
                client_phone=client_phone,
                started_at=datetime.utcnow(),
                message_count=0
            )
            session.add(active_session)
            
        active_session.message_count += 2  # user message + agent reply
        if escalated:
            active_session.escalated = True
            
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            # It's possible the Client record wasn't fully created yet in DB transaction if onboarding failed,
            # but we catch it to prevent blocking the chat response.
            pass

        return active_session
