from datetime import datetime
import pytz
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from src.agent.state import AgentState
from src.agent.tools import all_tools
from src.agent.prompts.system_prompt import SYSTEM_PROMPT
from config import Config


# ─── Constants ────────────────────────────────────────────────────────────────
SKIPPABLE_FIELDS = {"budget"}
MAX_ATTEMPTS = 3
MAX_TOOL_LOOPS = 20      # hard cap on tool→llm cycles per turn


def _build_onboarding_context(state: AgentState) -> str:
    """
    Returns a string with onboarding instructions to be injected into the system prompt.
    Empty string if onboarding is complete or no missing fields.
    """
    if state.get("onboarding_complete", False):
        return ""

    missing = state.get("onboarding_missing_fields", [])
    if not missing:
        return ""

    attempts = state.get("onboarding_attempts", {})

    field_labels = {
        "name":   "their full name",
        "city":   "which city or area in Florida they want",
        "intent": "whether they want to buy, rent, or invest",
        "budget": "their rough budget range",
    }

    # Build the ordered list — name is always first if missing
    ordered_missing = []
    if "name" in missing:
        ordered_missing.append("name")
    for f in missing:
        if f != "name" and f not in ordered_missing:
            ordered_missing.append(f)

    lines = []
    for f in ordered_missing:
        # Skip fields that have reached max attempts (only skippable ones)
        if f in SKIPPABLE_FIELDS and attempts.get(f, 0) >= MAX_ATTEMPTS:
            continue
        count = attempts.get(f, 0)
        lines.append(f"  - {field_labels[f]} (asked {count} time(s) so far)")

    if not lines:
        return ""

    # Name-specific emphasis when name is the first missing field
    name_rule = ""
    if ordered_missing and ordered_missing[0] == "name":
        name_rule = """
CRITICAL: The client's name is UNKNOWN. Your VERY FIRST priority is to warmly ask for their name.
Do NOT ask about city, intent, budget, or anything else until you have their name.
Example: "Hey there! Welcome to Riley Estate 🏡 I'm Friday, your real estate assistant. Before we get started, what should I call you?"
"""

    return f"""
═══════════════════════════════════════════════════════════
ONBOARDING IN PROGRESS
═══════════════════════════════════════════════════════════
{name_rule}
Still need to collect:
{chr(10).join(lines)}

Rules:
- Ask for the FIRST field above only — never ask multiple at once
- Be warm and conversational — this is WhatsApp, not a form
- If the client expressed frustration or anger → acknowledge it first, skip asking this turn
- If the client asked for a human agent → handle escalation immediately via escalation_logger, do NOT ask profile questions
- If the client said they don't know their budget → warmly accept it and move on
- Never repeat the exact same phrasing as a previous turn
- Never mention you are collecting data or filling a form
- Never skip ahead to property recommendations before collecting name, city, and intent
"""


async def llm_node(state: AgentState) -> dict:
    """
    Core reasoning node.
    Assembles full context into system prompt, binds all tools,
    calls Groq asynchronously, returns tool call or final response.
    """

    # ─── Active documents context ─────────────────────────────────────────
    active_docs_text = ""
    if state.get("active_documents"):
        docs = state["active_documents"]
        lines = []
        for doc_id, meta in docs.items():
            storage = meta.get("storage", "chunked")
            lines.append(
                f"- {meta['filename']} (doc_id: {doc_id}, storage: {storage})"
            )
        active_docs_text = "Documents available this session:\n" + "\n".join(lines)
        if any(m.get("storage") == "chunked" for m in docs.values()):
            active_docs_text += (
                "\nUse the document_search tool with the correct doc_id "
                "to query any chunked document."
            )

    # ─── Injected document text (small docs only) ─────────────────────────
    injected_doc = ""
    if state.get("injected_document_text"):
        injected_doc = (
            "\n\nDocument content (read directly — no tool needed):\n"
            f"{state['injected_document_text']}"
        )

    # ─── Onboarding context ───────────────────────────────────────────────
    onboarding_context = _build_onboarding_context(state)

    # ─── Assemble system prompt ───────────────────────────────────────────
    system_prompt = SYSTEM_PROMPT.format(
        summary=state.get("summary") or "No previous conversation summary.",
        memory_context=state.get("memory_context") or "No memories retrieved.",
        current_datetime=datetime.now(pytz.timezone(Config.AGENT_TIMEZONE)).strftime("%A, %B %d %Y %I:%M %p"),
        client_name=state.get("client_name") or "UNKNOWN — ask for their name first",
        client_phone=state.get("client_phone") or "UNKNOWN",
        client_email=state.get("client_email") or "Not provided yet — ask before booking a meeting",
        client_timezone=state.get("client_timezone") or "UTC",
        active_documents=active_docs_text,
        injected_document=injected_doc
    )

    # Inject onboarding instructions if needed
    if onboarding_context:
        system_prompt += onboarding_context

    # ─── Call Anthropic with all tools bound ───────────────────────────────────
    llm = ChatAnthropic(
        model=Config.ANTHROPIC_MODEL,
        temperature=0.3,
        api_key=Config.ANTHROPIC_API_KEY
    ).bind_tools(all_tools)

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    response = await llm.ainvoke(messages)

    # ─── Track tool call count for loop guard ─────────────────────────────
    tool_count = state.get("tool_call_count", 0)
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_count += len(response.tool_calls)

    return {
        "messages": [response],
        "tool_call_count": tool_count,
    }


def route_after_llm(state: AgentState) -> str:
    last_message = state["messages"][-1]

    # ─── Tool loop guard — prevent runaway tool cycles ────────────────────
    if state.get("tool_call_count", 0) >= MAX_TOOL_LOOPS:
        return "response_node"

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"
    return "response_node"