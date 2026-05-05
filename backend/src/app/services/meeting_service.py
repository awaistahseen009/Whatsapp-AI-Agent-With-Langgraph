from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.meeting import Meeting, MeetingStatus
from src.app.models.conversation_session import ConversationSession
from src.app.models.transcript import Transcript
from src.app.schemas.meeting_schema import MeetingUpdateSchema, MeetingCreateSchema
from src.app.services.chat_service import ChatService
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json


class MeetingService:
    async def create_meeting(self, data: MeetingCreateSchema, session: AsyncSession):
        end_time = data.start_time + timedelta(minutes=data.duration_minutes)
        meeting = Meeting(
            client_phone=data.client_phone,
            meeting_type=data.meeting_type,
            meeting_format=data.meeting_format,
            start_time=data.start_time,
            end_time=end_time,
            duration_minutes=data.duration_minutes,
            client_timezone=data.client_timezone,
            notes=data.notes,
            zoom_meeting_id=data.zoom_meeting_id,
            zoom_join_url=data.zoom_join_url,
            status=MeetingStatus.SCHEDULED,
        )
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting

    async def list_meetings(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(Meeting).order_by(Meeting.start_time.desc())
        if client_phone:
            statement = statement.where(Meeting.client_phone == client_phone)
        if status:
            statement = statement.where(Meeting.status == status)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_meeting(self, meeting_id: str, session: AsyncSession):
        statement = select(Meeting).where(Meeting.meeting_id == meeting_id)
        result = await session.exec(statement)
        return result.first()

    async def update_meeting(self, meeting_id: str, data: MeetingUpdateSchema, session: AsyncSession):
        meeting = await self.get_meeting(meeting_id, session)
        if not meeting:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(meeting, key, value)
        if data.status == "cancelled":
            meeting.cancelled_at = datetime.now()
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting

    async def get_meeting_details(self, meeting_id: str, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get meeting details with conversation summary and transcripts"""
        meeting = await self.get_meeting(meeting_id, session)
        if not meeting:
            return None

        # Get conversation session for this client around the meeting time
        meeting_date = meeting.start_time.date()
        start_of_day = datetime.combine(meeting_date, datetime.min.time())
        end_of_day = datetime.combine(meeting_date, datetime.max.time())

        session_statement = select(ConversationSession).where(
            ConversationSession.client_phone == meeting.client_phone,
            ConversationSession.started_at >= start_of_day,
            ConversationSession.started_at <= end_of_day
        ).order_by(ConversationSession.started_at.desc())
        
        session_result = await session.exec(session_statement)
        conversation_session = session_result.first()

        transcripts = []
        summary = meeting.conversation_summary

        if conversation_session:
            chat_service = ChatService()
            transcripts = await chat_service.get_session_transcripts(conversation_session.session_id, session)
            
            # If no summary exists, generate one from transcripts
            if not summary and transcripts:
                summary = await self._generate_summary_from_transcripts(transcripts)
                # Save the summary to the meeting
                meeting.conversation_summary = summary
                session.add(meeting)
                await session.commit()

        return {
            **meeting.model_dump(),
            "conversation_session": conversation_session.model_dump() if conversation_session else None,
            "transcripts": [t.model_dump() for t in transcripts],
            "generated_summary": summary
        }

    async def _generate_summary_from_transcripts(self, transcripts) -> str:
        """Generate a summary from conversation transcripts using OpenAI API"""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            from config import config
            
            if not getattr(config, "OPENAI_API_KEY", None):
                return f"Fall-back simple summary: Conversation lasted {len(transcripts)} total messages."

            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", api_key=config.OPENAI_API_KEY)
            
            chat_history = ""
            for t in transcripts[-50:]: # cap at last 50
                chat_history += f"{t.message_type.upper()}: {t.message_content}\n"
                
            messages = [
                SystemMessage(content="You are an expert AI assistant context engine for Riley Estate. Provide a structured, coherent 1-paragraph summary of the following WhatsApp conversation between an AI Agent and a Client. Focus on their real estate intent, constraints, and why a meeting was scheduled. Refrain from using markdown bold tags or bullets."),
                HumanMessage(content=chat_history)
            ]
            response = await llm.ainvoke(messages)
            return str(response.content)
        except Exception as e:
            print(f"Summarization error: {e}")
            return f"Conversation spanned {len(transcripts)} messages."

    async def cancel_meeting(self, meeting_id: str, reason: str, session: AsyncSession):
        meeting = await self.get_meeting(meeting_id, session)
        if not meeting:
            return None
        meeting.status = MeetingStatus.CANCELLED
        meeting.cancelled_at = datetime.now()
        meeting.cancellation_reason = reason
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting
