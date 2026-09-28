import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/chat")
async def post_chat(body: ChatRequest):
    # TODO: wire this to app/services/assistant_service.py once it exists
    logger.info(f"Received chat message (assistant not wired yet): {body.message!r}")
    return JSONResponse(
        content={"error": "NOT_IMPLEMENTED", "message": "The assistant is not built yet"},
        status_code=501,
    )
