# src/graph/main.py

import asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.graph.graph import build_graph
from config import Config
import sys

# ─── Fake WhatsApp webhook payload ───────────────────────────────────────────

def make_text_payload(phone: str, message: str) -> dict:
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": phone,
                        "type": "text",
                        "text": {"body": message}
                    }]
                }
            }]
        }]
    }


def make_document_payload(phone: str, media_id: str, filename: str, caption: str = "") -> dict:
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": phone,
                        "type": "document",
                        "document": {
                            "id": media_id,
                            "filename": filename,
                            "caption": caption
                        }
                    }]
                }
            }]
        }]
    }


# ─── Run a single turn ────────────────────────────────────────────────────────

async def run_turn(graph, phone: str, payload: dict):
    config = {
        "configurable": {
            "thread_id": phone,
            "incoming_payload": payload
        }
    }

    print(f"\n{'─' * 60}")
    print(f"INPUT  → {payload['entry'][0]['changes'][0]['value']['messages'][0]}")
    print(f"{'─' * 60}")

    result = await graph.ainvoke(
        {"messages": []},
        config=config
    )

    # print last AI message
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            if not hasattr(msg, "tool_calls"):
                print(f"FRIDAY → {msg.content}")
                break
            elif not msg.tool_calls:
                print(f"FRIDAY → {msg.content}")
                break

    print(f"response_type  : {result.get('response_type', 'N/A')}")
    print(f"message_count  : {result.get('message_count', 0)}")
    print(f"onboarding     : {result.get('onboarding_complete', False)}")
    print(f"client_name    : {result.get('client_name', '')}")
    print(f"client_timezone: {result.get('client_timezone', '')}")
    print(f"escalated      : {result.get('escalated', False)}")
    print(f"active_docs    : {list(result.get('active_documents', {}).keys())}")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    phone = "27051234567"

    async with AsyncPostgresSaver.from_conn_string(Config.LANGGRAPH_CHECKPOINT_DB_URL) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)

        print("\n" + "═" * 60)
        print("  GRAPH TEST — Riley Estate WhatsApp Agent")
        print("═" * 60)
        print("  Type your message and press Enter. Type 'exit' to quit.")
        print("═" * 60)

        while True:
            try:
                user_input = input("\nYOU → ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if user_input.lower() == "exit":
                print("Exiting...")
                break

            if not user_input:
                continue

            await run_turn(graph, phone, make_text_payload(phone, user_input))


from asyncio import WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
if __name__ == "__main__":
    asyncio.run(main())