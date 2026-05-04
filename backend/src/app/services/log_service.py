from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.logs import TokenLog, ToolExecutionLog, ErrorLog
from typing import Optional


class LogService:
    async def list_token_logs(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ):
        statement = select(TokenLog).order_by(TokenLog.created_at.desc())
        if client_phone:
            statement = statement.where(TokenLog.client_phone == client_phone)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def list_tool_logs(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        tool_name: Optional[str] = None,
        success: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ):
        statement = select(ToolExecutionLog).order_by(ToolExecutionLog.created_at.desc())
        if client_phone:
            statement = statement.where(ToolExecutionLog.client_phone == client_phone)
        if tool_name:
            statement = statement.where(ToolExecutionLog.tool_name == tool_name)
        if success is not None:
            statement = statement.where(ToolExecutionLog.success == success)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def list_error_logs(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ):
        statement = select(ErrorLog).order_by(ErrorLog.created_at.desc())
        if client_phone:
            statement = statement.where(ErrorLog.client_phone == client_phone)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()
