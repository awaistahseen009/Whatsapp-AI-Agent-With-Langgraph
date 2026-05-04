"""
Launch the FastAPI server with the correct event loop policy for Windows.
Usage: python run_server.py
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
