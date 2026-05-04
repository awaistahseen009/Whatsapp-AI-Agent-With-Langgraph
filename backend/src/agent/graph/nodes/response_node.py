import json
import random
from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel, Field, ValidationError

from src.agent.state import AgentState


class FinalResponse(BaseModel):
    response_type: Literal["text", "audio"] = Field(
        description="How WhatsApp should deliver the response."
    )
    content: str = Field(description="The final reply text to send to the client.")


def _strip_legacy_prefix(content: str) -> str:
    lowered = content.lower()
    if lowered.startswith("audio:"):
        return content[len("audio:"):].strip()
    if lowered.startswith("text:"):
        return content[len("text:"):].strip()
    return content.strip()


def _parse_final_response(content) -> FinalResponse:
    if isinstance(content, list):
        text_blocks = [
            block["text"] 
            for block in content 
            if isinstance(block, dict) and block.get("type") == "text" and "text" in block
        ]
        if text_blocks:
            content = "\n".join(text_blocks)
        elif content and isinstance(content[0], str):
            content = "\n".join(content)
        else:
            content = str(content)
            
    if not isinstance(content, str):
        content = str(content)

    clean = _strip_legacy_prefix(content)
    try:
        parsed = json.loads(clean)
        return FinalResponse.model_validate(parsed)
    except (json.JSONDecodeError, TypeError, ValidationError):
        return FinalResponse(response_type="text", content=clean)


def _check_escalation(messages: list) -> bool:
    """Scan recent messages for an escalation_logger tool call that succeeded."""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "escalation_logger":
            content = msg.content if hasattr(msg, "content") else ""
            if "successfully" in content.lower():
                return True
        if hasattr(msg, "type") and msg.type == "human":
            break
    return False


async def response_node(state: AgentState) -> dict:
    """
    Parses the final LLM message. The LLM already chose response_type in the
    same call that generated the reply, so this node does not call another LLM.
    """
    last_message = state["messages"][-1]
    raw_content = last_message.content if hasattr(last_message, "content") else ""
    final_response = _parse_final_response(raw_content)

    response_type = final_response.response_type
    if response_type == "text" and random.random() < 0.4:
        response_type = "audio"

    updates: dict = {
        "response_type": response_type,
        "tool_call_count": 0,
    }

    if _check_escalation(state["messages"]):
        updates["escalated"] = True

    if final_response.content != raw_content:
        updates["messages"] = [AIMessage(content=final_response.content)]

    return updates


def route_after_response(state: AgentState) -> str:
    if state.get("message_count", 0) >= 20:
        return "summarize_node"
    return "END"
