from src.agent.state import AgentState
from src.agent.modules.memory.long_term_client_memory import search_client_memories


async def memory_retrieval_node(state: AgentState) -> dict:
    """
    Searches ChromaDB client_memories for facts relevant to the incoming message.
    Uses the latest human message as the semantic query.
    Assembles results into memory_context string ready for system prompt injection.
    Re-fetched fresh every turn — never persisted to checkpointer.
    """
    phone = state["client_phone"]
    last_message = state["messages"][-1].content if state["messages"] else ""

    # skip media placeholders — no point searching for "[Client sent an image]"
    if not last_message or last_message.startswith("[Client sent"):
        return {
            "retrieved_memories": [],
            "memory_context": ""
        }

    memories = search_client_memories(
        phone_number=phone,
        query=last_message,
        k=6
    )

    memory_context = "\n".join(f"- {m}" for m in memories) if memories else ""

    return {
        "retrieved_memories": memories,
        "memory_context": memory_context
    }