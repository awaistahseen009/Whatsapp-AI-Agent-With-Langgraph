from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.conversation_session import ConversationSession
from src.app.models.transcript import Transcript
from typing import Optional
import asyncio
import uuid


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

    async def save_transcript_async(
        self,
        session_id: uuid.UUID,
        client_phone: str,
        message_content: str,
        message_type: str,
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Fire-and-forget transcript saving - runs in background without blocking"""
        try:
            from src.db.session import get_async_session
            
            async with get_async_session() as db_session:
                transcript = Transcript(
                    session_id=session_id,
                    client_phone=client_phone,
                    message_content=message_content,
                    message_type=message_type,
                    tokens_used=tokens_used,
                    processing_time_ms=processing_time_ms
                )
                db_session.add(transcript)
                await db_session.commit()
        except Exception as e:
            # Log error but don't raise - this is fire-and-forget
            print(f"Failed to save transcript: {e}")

    def save_transcript_fire_and_forget(
        self,
        session_id: uuid.UUID,
        client_phone: str,
        message_content: str,
        message_type: str,
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ):
        """Non-blocking transcript save - creates background task"""
        asyncio.create_task(
            self.save_transcript_async(
                session_id=session_id,
                client_phone=client_phone,
                message_content=message_content,
                message_type=message_type,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms
            )
        )

    async def get_session_transcripts(
        self,
        session_id: uuid.UUID,
        session: AsyncSession
    ):
        """Get all transcripts for a session"""
        statement = select(Transcript).where(
            Transcript.session_id == session_id
        ).order_by(Transcript.created_at.asc())
        result = await session.exec(statement)
        return result.all()

    async def get_sessions_by_date_range(self, session: AsyncSession, start_date, end_date):
        """Get sessions created within a date range"""
        statement = select(ConversationSession).where(
            ConversationSession.started_at >= start_date,
            ConversationSession.started_at <= end_date
        ).order_by(ConversationSession.started_at.desc())
        result = await session.exec(statement)
        return result.all()
