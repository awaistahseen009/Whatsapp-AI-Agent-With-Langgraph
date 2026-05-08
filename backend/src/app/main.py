import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.routes.user_router import auth_router
from src.app.routes.property_router import property_router
from src.app.routes.meeting_router import meeting_router
from src.app.routes.escalation_router import escalation_router
from src.app.routes.log_router import log_router
from src.app.routes.client_router import client_router
from src.app.routes.chat_router import chat_router
from src.app.routes.document_router import document_router
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.graph.graph import build_graph 
from contextlib import asynccontextmanager
from config import Config

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        Config.LANGGRAPH_CHECKPOINT_DB_URL
    ) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer)
        yield

app = FastAPI(
    title="Riley Estate API",
    description="Backend API for Riley Estate — real estate agency dashboard",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this, but * works for all Vite network urls
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register routers ────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(property_router, prefix="/api/properties", tags=["Properties"])
app.include_router(meeting_router, prefix="/api/meetings", tags=["Meetings"])
app.include_router(escalation_router, prefix="/api/escalations", tags=["Escalations"])
app.include_router(log_router, prefix="/api/logs", tags=["Logs"])
app.include_router(client_router, prefix="/api/clients", tags=["Clients"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(document_router, prefix="/api/documents", tags=["Documents"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "Riley Estate API"}
