import logging
from contextlib import asynccontextmanager, AsyncExitStack

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.routes import chat
from app.services import mcp_client
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting Order Management Assistant, using model {settings.openai_model}")
    async with AsyncExitStack() as stack:
        server_params = StdioServerParameters(command="venv/Scripts/python.exe", args=["-m", "app.mcp_server.server"])
        read, write = await stack.enter_async_context(stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        mcp_client.set_session(session)
        logger.info("MCP Toolbox connected")
        yield
    logger.info("Application shutting down")


app = FastAPI(title="Order Management Assistant", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error handling {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
        status_code=500,
    )


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(chat.router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")