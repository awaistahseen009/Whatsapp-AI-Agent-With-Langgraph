from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, RemoveMessage
from pydantic import BaseModel, Field
from src.agent.state import AgentState
from src.agent.modules.memory.long_term_client_memory import store_client_memory
from config import Config


class ExtractedMemories(BaseModel):
    preferences: list[str] = Field(
        default_factory=list,
        description="Property or service preferences explicitly stated by the client"
    )
    rejections: list[str] = Field(
        default_factory=list,
        description="Things the client explicitly rejected or said no to"
    )
    personal: list[str] = Field(
        default_factory=list,
        description="Personal facts like family size, job, lifestyle, location needs"
    )
    financial: list[str] = Field(
        default_factory=list,
        description="Budget, loan status, financial constraints or pre-approvals"
    )
    properties_viewed: list[str] = Field(
        default_factory=list,
        description="Specific properties discussed, viewed, or considered"
    )


def _format_conversation(messages: list) -> str:
    lines = []
    for m in messages:
        if not hasattr(m, "content") or not m.content:
            continue
        if m.content.startswith("["):
            continue
        role = "Client" if isinstance(m, HumanMessage) else "Friday"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


async def summarize_node(state: AgentState) -> dict:
    """
    Fires when message_count >= 20.

    Flow:
    1. Format messages into raw conversation text.
    2. LLM call 1: extract structured facts.
    3. LLM call 2: compress into rolling summary.
    4. Embed each fact enriched with raw conversation context into ChromaDB.
    5. Store rolling summary itself as a memory.
    6. Prune messages keeping last 5 using RemoveMessage.
    7. Reset message_count to 0.
    """
    phone = state["client_phone"]
    messages = state["messages"]
    existing_summary = state.get("summary", "")

    raw_conversation = _format_conversation(messages)

    llm = ChatGroq(
        model=Config.GROQ_MODEL,
        temperature=0,
        api_key=Config.GROQ_API_KEY
    )

    # ─── Call 1: structured fact extraction ──────────────────────────────
    from src.agent.utils.retry import retry_structured_output
    import json

    json_llm = ChatGroq(
        model=Config.GROQ_MODEL,
        temperature=0,
        api_key=Config.GROQ_API_KEY
    ).bind(
        response_format={"type": "json_object"}
    )

    schema_hint = json.dumps(ExtractedMemories.model_json_schema(), indent=2)

    @retry_structured_output(max_attempts=5)
    async def _extract_memories(msgs):
        response = await json_llm.ainvoke(msgs)
        return ExtractedMemories.model_validate_json(response.content)

    extracted: ExtractedMemories = await _extract_memories([
        (
            "system",
            "You are a strict JSON data extraction processor. "
            "You MUST respond with ONLY a valid JSON object — no text, no greetings, no explanation. "
            "Extract memorable facts from the real estate conversation below. "
            "Each fact must be a single clear sentence. "
            "Only extract what the client explicitly stated — do not infer. "
            "Be specific: 'Client rejected Unit 4B because of noise' "
            "not 'Client rejected a unit'.\n\n"
            f"Output MUST match this JSON schema:\n{schema_hint}"
        ),
        ("human", f"Conversation:\n{raw_conversation}")
    ])

    # ─── Call 2: rolling summary compression ─────────────────────────────
    summary_response = await llm.ainvoke([
        (
            "system",
            "You are compressing a real estate conversation into a concise rolling summary. "
            "Preserve: client preferences, rejections, budget, properties discussed, "
            "commitments made, and personal facts relevant to the property search. "
            "Discard: greetings, filler, repetition. "
            "Merge with the existing summary — do not repeat what is already captured. "
            "Output only the summary text. Max 200 words."
        ),
        (
            "human",
            f"Existing summary:\n{existing_summary}\n\n"
            f"New conversation:\n{raw_conversation}"
        )
    ])

    new_summary = summary_response.content.strip()

    # ─── Store each fact enriched with raw conversation context ──────────
    memory_map = {
        "preference":      extracted.preferences,
        "rejection":       extracted.rejections,
        "personal":        extracted.personal,
        "financial":       extracted.financial,
        "property_viewed": extracted.properties_viewed,
    }

    for memory_type, facts in memory_map.items():
        for fact in facts:
            if fact.strip():
                store_client_memory(
                    phone_number=phone,
                    fact=fact.strip(),
                    raw_context=raw_conversation,
                    memory_type=memory_type
                )

    # store rolling summary as a memory too
    if new_summary:
        store_client_memory(
            phone_number=phone,
            fact=new_summary,
            raw_context=raw_conversation,
            memory_type="summary"
        )

    # ─── Prune messages keeping last 5 ───────────────────────────────────
    messages_to_remove = [
        RemoveMessage(id=m.id)
        for m in messages[:-5]
        if hasattr(m, "id") and m.id
    ]

    return {
        "summary": new_summary,
        "messages": messages_to_remove,
        "message_count": 0,
        "retrieved_memories": [],
        "memory_context": "",
    }