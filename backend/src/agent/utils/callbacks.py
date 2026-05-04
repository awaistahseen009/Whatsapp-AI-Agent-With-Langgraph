from typing import Dict, Any, List, Optional
import uuid
import time
from uuid import UUID
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from src.db.session import get_async_session
from src.app.models.logs import TokenLog, ToolExecutionLog

class AgentLoggingCallback(AsyncCallbackHandler):
    """
    Callback handler to log LLM token usage and Tool execution directly to the database.
    """
    def __init__(self, client_phone: str, session_id: uuid.UUID):
        super().__init__()
        self.client_phone = client_phone
        self.session_id = session_id
        self.tool_starts: Dict[str, float] = {}
        self.llm_starts: Dict[str, float] = {}

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.tool_starts[str(run_id)] = time.time()

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        start_time = self.tool_starts.pop(str(run_id), time.time())
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        tool_name = kwargs.get("name", "unknown_tool")

        async with get_async_session() as session:
            log = ToolExecutionLog(
                client_phone=self.client_phone,
                session_id=self.session_id,
                tool_name=tool_name,
                success=True,
                error_message=None,
                execution_time_ms=execution_time_ms
            )
            session.add(log)
            # Handle silently if DB is locked or fails
            try:
                await session.commit()
            except Exception:
                await session.rollback()

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        start_time = self.tool_starts.pop(str(run_id), time.time())
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        tool_name = kwargs.get("name", "unknown_tool")

        async with get_async_session() as session:
            log = ToolExecutionLog(
                client_phone=self.client_phone,
                session_id=self.session_id,
                tool_name=tool_name,
                success=False,
                error_message=str(error),
                execution_time_ms=execution_time_ms
            )
            session.add(log)
            try:
                await session.commit()
            except Exception:
                await session.rollback()

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.llm_starts[str(run_id)] = time.time()

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        start_time = self.llm_starts.pop(str(run_id), time.time())
        latency_ms = int((time.time() - start_time) * 1000)
        
        if not response.llm_output or "token_usage" not in response.llm_output:
            return

        token_usage = response.llm_output["token_usage"]
        tokens_in = token_usage.get("prompt_tokens", 0)
        tokens_out = token_usage.get("completion_tokens", 0)
        model_name = response.llm_output.get("model_name", "unknown_model")

        # Basic cost estimation (can be moved to config if needed)
        cost_usd = (tokens_in * 0.0000000) + (tokens_out * 0.0000000) # Open source models mostly free

        async with get_async_session() as session:
            log = TokenLog(
                client_phone=self.client_phone,
                session_id=self.session_id,
                node_name=model_name,
                model_name=model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                cost_usd=cost_usd
            )
            session.add(log)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
