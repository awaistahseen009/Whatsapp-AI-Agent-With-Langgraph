import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.graph.graph import build_graph
from config import Config

# ─── Logging Setup ────────────────────────────────────────────────────────────

Path("logs").mkdir(exist_ok=True)

log_filename = f"logs/agent_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)


# ─── Patch fetch_media_bytes to read from local file during testing ───────────
# Remove this block when moving to production

import src.agent.graph.nodes.document_node as _doc_module

async def _fake_fetch_media_bytes(media_id: str) -> bytes:
    with open("sample_docs/test.pdf", "rb") as f:
        return f.read()

_doc_module.fetch_media_bytes = _fake_fetch_media_bytes


# ─── Payload Builders ─────────────────────────────────────────────────────────

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


def make_document_payload(
    phone: str,
    media_id: str,
    filename: str,
    caption: str = ""
) -> dict:
    msg = {
        "from": phone,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename,
        }
    }
    if caption:
        msg["document"]["caption"] = caption
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [msg]
                }
            }]
        }]
    }


# ─── State Printer ────────────────────────────────────────────────────────────

def print_state(result: dict, label: str = "") -> None:
    if label:
        log.info(f"\n{'═' * 60}")
        log.info(f"  {label}")
        log.info(f"{'═' * 60}")

    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
            if not has_tool_calls:
                log.info(f"\nFRIDAY → {msg.content}")
                break

    summary = result.get("summary", "")
    memory_context = result.get("memory_context", "")

    log.info(f"\n{'─' * 40}")
    log.info(f"response_type  : {result.get('response_type', 'N/A')}")
    log.info(f"message_count  : {result.get('message_count', 0)}")
    log.info(f"onboarding     : {result.get('onboarding_complete', False)}")
    log.info(f"client_name    : {result.get('client_name', '')}")
    log.info(f"client_timezone: {result.get('client_timezone', '')}")
    log.info(f"escalated      : {result.get('escalated', False)}")
    log.info(f"summary        : {summary[:80]}{'...' if len(summary) > 80 else ''}")
    log.info(f"active_docs    : {list(result.get('active_documents', {}).keys())}")
    log.info(f"memory_context : {memory_context[:80]}{'...' if len(memory_context) > 80 else ''}")
    log.info(f"{'─' * 40}")


# ─── Turn Runners ─────────────────────────────────────────────────────────────

async def run_turn_text(graph, phone: str, message: str) -> dict:
    payload = make_text_payload(phone, message)

    log.info(f"\nYOU (text) → {message}")
    log.info(f"timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = {
        "configurable": {
            "thread_id": phone,
            "incoming_payload": payload
        }
    }

    result = await graph.ainvoke(
        {"messages": []},
        config=config
    )

    print_state(result)
    return result


async def run_turn_doc_with_caption(
    graph,
    phone: str,
    media_id: str,
    filename: str,
    caption: str
) -> dict:
    """Document sent with a caption question attached."""
    payload = make_document_payload(
        phone=phone,
        media_id=media_id,
        filename=filename,
        caption=caption
    )

    log.info(f"\nYOU (document + caption) → [{filename}] {caption}")
    log.info(f"timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = {
        "configurable": {
            "thread_id": phone,
            "incoming_payload": payload
        }
    }

    result = await graph.ainvoke(
        {"messages": []},
        config=config
    )

    print_state(result, label="Document + Caption Turn")
    return result


async def run_turn_doc_only(
    graph,
    phone: str,
    media_id: str,
    filename: str
) -> dict:
    """Document sent with no caption — agent acknowledges and waits for question."""
    payload = make_document_payload(
        phone=phone,
        media_id=media_id,
        filename=filename,
        caption=""
    )

    log.info(f"\nYOU (document only) → [{filename}]")
    log.info(f"timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = {
        "configurable": {
            "thread_id": phone,
            "incoming_payload": payload
        }
    }

    result = await graph.ainvoke(
        {"messages": []},
        config=config
    )

    print_state(result, label="Document Only Turn")
    return result


# ─── Interactive Mode ─────────────────────────────────────────────────────────

async def run_interactive(graph, phone: str) -> None:
    log.info("\n" + "═" * 60)
    log.info("  INTERACTIVE MODE — type messages and press Enter")
    log.info("  Type 'exit' to quit")
    log.info("═" * 60)

    while True:
        try:
            user_input = input("\nYOU → ").strip()
        except (EOFError, KeyboardInterrupt):
            log.info("\nExiting...")
            break

        if user_input.lower() == "exit":
            log.info("Exiting...")
            break

        if not user_input:
            continue

        await run_turn_text(graph, phone, user_input)


# ─── Test Scenarios ───────────────────────────────────────────────────────────

async def run_all_scenarios(graph, phone: str) -> None:
    """
    Runs all test scenarios sequentially:
      1. Onboarding text conversation
      2. Property search query
      3. Document with caption (question embedded)
      4. Document only (no caption)
      5. Follow-up question about the document
      6. Scheduling request
      7. Escalation trigger
    """

    FAKE_MEDIA_ID = "fake_media_id_12345"
    DOC_FILENAME  = "test.pdf"

    # ── Scenario 1 — Onboarding ───────────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 1 — Onboarding")
    log.info("═" * 60)

    await run_turn_text(graph, phone, "Hello")
    await asyncio.sleep(10)

    await run_turn_text(graph, phone, "My name is Alex Johnson")
    await asyncio.sleep(10)

    await run_turn_text(graph, phone, "I am based in Miami")
    await asyncio.sleep(10)

    await run_turn_text(graph, phone, "Looking to buy")
    await asyncio.sleep(10)

    await run_turn_text(graph, phone, "Budget is around 600k to 900k")
    await asyncio.sleep(10)

    # ── Scenario 2 — Property Search ─────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 2 — Property Search")
    log.info("═" * 60)

    await run_turn_text(
        graph, phone,
        "Can you show me 3 bedroom villas in Miami under 800k?"
    )
    await asyncio.sleep(10)

    await run_turn_text(
        graph, phone,
        "I don't want anything on the ground floor, I have young kids"
    )
    await asyncio.sleep(10)

    await run_turn_text(
        graph, phone,
        "What are Riley Estate's commission rates?"
    )
    await asyncio.sleep(10)

    # ── Scenario 3 — Document With Caption ───────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 3 — Document With Caption")
    log.info("  (document + question sent together)")
    log.info("═" * 60)

    await run_turn_doc_with_caption(
        graph=graph,
        phone=phone,
        media_id=FAKE_MEDIA_ID,
        filename=DOC_FILENAME,
        caption="Can you check what the possession date is in this agreement?"
    )
    await asyncio.sleep(10)

    # ── Scenario 4 — Document Only ────────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 4 — Document Only")
    log.info("  (no caption — agent should acknowledge and ask what they need)")
    log.info("═" * 60)

    await run_turn_doc_only(
        graph=graph,
        phone=phone,
        media_id=FAKE_MEDIA_ID,
        filename=DOC_FILENAME,
    )
    await asyncio.sleep(10)

    # ── Scenario 5 — Follow-up Questions About Document ───────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 5 — Follow-up Questions About Document")
    log.info("═" * 60)

    await run_turn_text(
        graph, phone,
        "What does the document say about the payment schedule?"
    )
    await asyncio.sleep(10)

    await run_turn_text(
        graph, phone,
        "Is there any penalty clause mentioned?"
    )
    await asyncio.sleep(10)

    # ── Scenario 6 — Scheduling ───────────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 6 — Scheduling")
    log.info("═" * 60)

    await run_turn_text(
        graph, phone,
        "I would like to schedule a property viewing this Saturday at 3pm"
    )
    await asyncio.sleep(10)

    await run_turn_text(
        graph, phone,
        "Yes that time works for me, please go ahead and book it"
    )
    await asyncio.sleep(10)

    # ── Scenario 7 — Escalation ───────────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  SCENARIO 7 — Escalation Trigger")
    log.info("═" * 60)

    await run_turn_text(
        graph, phone,
        "I need to speak to a human agent please"
    )
    await asyncio.sleep(10)

    log.info("\n" + "═" * 60)
    log.info("  ALL SCENARIOS COMPLETE")
    log.info("═" * 60)


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    phone = "12345678901"

    log.info("\n" + "═" * 60)
    log.info("  Riley Estate — WhatsApp Agent Test Runner")
    log.info("═" * 60)
    log.info(f"  Phone number under test : {phone}")
    log.info(f"  Test document           : sample_docs/test.pdf")
    log.info(f"  fetch_media_bytes       : PATCHED (reading local file)")
    log.info(f"  Log file                : {log_filename}")
    log.info(f"  Session started         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("═" * 60)

    async with AsyncPostgresSaver.from_conn_string(
        Config.LANGGRAPH_CHECKPOINT_DB_URL
    ) as checkpointer:
        await checkpointer.setup()
        graph = build_graph(checkpointer)

        # run all scripted scenarios first
        await run_all_scenarios(graph, phone)

        # then drop into interactive mode for manual testing
        await run_interactive(graph, phone)

    log.info("\n" + "═" * 60)
    log.info(f"  Session ended : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Full log saved to : {log_filename}")
    log.info("═" * 60)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(main())