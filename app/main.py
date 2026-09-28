import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import chat
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting Order Management Assistant, using model {settings.openai_model}")
    # TODO: launch the MCP server subprocess and open one MCP client session here,
    # the same AsyncExitStack pattern used in the previous MCP project, once
    # app/mcp_server/server.py actually has tools registered on it.
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
