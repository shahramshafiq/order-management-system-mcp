import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services import guardrails_service
from app.services.assistant_service import handle_message

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/chat")
async def post_chat(body: ChatRequest):
    is_safe_input = await guardrails_service.check_input(body.message)
    if not is_safe_input:
        logger.warning(f"Blocked unsafe input: {body.message!r}")
        return JSONResponse(
            content={"error": "BLOCKED_INPUT", "message": "I can't help with that request."},
            status_code=400,
        )

    try:
        result = await handle_message(body.message)
    except Exception:
        logger.exception(f"Failed to handle chat message: {body.message!r}")
        return JSONResponse(
            content={"error": "ASSISTANT_ERROR", "message": "The assistant could not process this message"},
            status_code=500,
        )

    is_safe_output = await guardrails_service.check_output(body.message, result["answer"])
    if not is_safe_output:
        logger.warning(f"Blocked unsafe output for message: {body.message!r}")
        return JSONResponse(
            content={"error": "BLOCKED_OUTPUT", "message": "I can't share that response."},
            status_code=400,
        )

    return {"message": body.message, "answer": result["answer"], "tool_calls": result["tool_calls"]}