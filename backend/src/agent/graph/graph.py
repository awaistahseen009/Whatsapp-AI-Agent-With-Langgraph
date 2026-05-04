from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agent.state import AgentState
from src.agent.graph.nodes.input_node import input_node
from src.agent.graph.nodes.media_node import media_node
from src.agent.graph.nodes.profile_loader_node import profile_loader_node, route_after_profile
from src.agent.graph.nodes.onboarding_decide_node import onboarding_decide_node
from src.agent.graph.nodes.memory_retrieval_node import memory_retrieval_node
from src.agent.graph.nodes.document_node import document_node
from src.agent.graph.nodes.llm_node import llm_node, route_after_llm
from src.agent.graph.nodes.response_node import response_node, route_after_response
from src.agent.graph.nodes.summarize_node import summarize_node
from src.agent.tools import all_tools
from config import Config


def build_graph(checkpointer) -> StateGraph:
    builder = StateGraph(AgentState)

    # ─── Register nodes ───────────────────────────────────────────────────
    builder.add_node("input_node",             input_node)
    builder.add_node("media_node",             media_node)
    builder.add_node("profile_loader_node",    profile_loader_node)
    builder.add_node("onboarding_decide_node", onboarding_decide_node)
    builder.add_node("memory_retrieval_node",  memory_retrieval_node)
    builder.add_node("document_node",          document_node)
    builder.add_node("llm_node",               llm_node)
    builder.add_node("tool_node",              ToolNode(all_tools))
    builder.add_node("response_node",          response_node)
    builder.add_node("summarize_node",         summarize_node)

    # ─── Entry ────────────────────────────────────────────────────────────
    builder.set_entry_point("input_node")

    # ─── input → profile ──────────────────────────────────────────────────
    builder.add_edge("input_node", "media_node")
    builder.add_edge("media_node", "profile_loader_node")

    # ─── profile → onboarding OR memory ───────────────────────────────────
    builder.add_conditional_edges(
        "profile_loader_node",
        route_after_profile,
        {
            "onboarding_decide_node": "onboarding_decide_node",
            "memory_retrieval_node":  "memory_retrieval_node"
        }
    )

    # ─── onboarding → always through memory (returning clients need context) ──
    # both complete and incomplete onboarding go to memory_retrieval_node.
    # the llm_node reads onboarding_missing_fields and adjusts its behaviour.
    builder.add_edge("onboarding_decide_node", "memory_retrieval_node")

    # ─── memory → document → llm ──────────────────────────────────────────
    builder.add_edge("memory_retrieval_node", "document_node")
    builder.add_edge("document_node",         "llm_node")

    # ─── llm → tool loop OR response ─────────────────────────────────────
    builder.add_conditional_edges(
        "llm_node",
        route_after_llm,
        {
            "tool_node":     "tool_node",
            "response_node": "response_node"
        }
    )

    # ─── tool → llm loop ─────────────────────────────────────────────────
    # after every tool execution the LLM runs again to decide
    # whether to call another tool or produce the final response
    builder.add_edge("tool_node", "llm_node")

    # ─── response → summarize OR END ─────────────────────────────────────
    builder.add_conditional_edges(
        "response_node",
        route_after_response,
        {
            "summarize_node": "summarize_node",
            "END":            END
        }
    )

    # ─── summarize → END ─────────────────────────────────────────────────
    builder.add_edge("summarize_node", END)

    return builder.compile(checkpointer=checkpointer)


async def get_checkpointer():
    async with AsyncPostgresSaver.from_conn_string(Config.LANGGRAPH_CHECKPOINT_DB_URL) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
