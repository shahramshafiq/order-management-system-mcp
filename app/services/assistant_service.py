import json
from datetime import datetime

from openai import AsyncOpenAI

from app.config import settings
from app.services import conversation_memory, mcp_client
from app.services.prompts import SYSTEM_PROMPT_TEMPLATE

client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
MAX_TOOL_ROUNDS = 4


async def handle_message(user_message: str) -> dict:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        now=datetime.now().strftime("%A, %Y-%m-%d %H:%M"),
        currency=settings.currency,
    )
    messages = (
        [{"role": "system", "content": system_prompt}]
        + conversation_memory.get_history()
        + [{"role": "user", "content": user_message}]
    )
    tools = await mcp_client.get_openai_tools()
    tool_calls_made = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.chat.completions.create(model=settings.openai_model, messages=messages, tools=tools)
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            conversation_memory.remember(messages[1:])
            return {"answer": message.content, "tool_calls": tool_calls_made}

        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            tool_calls_made.append(name)
            print(f"LLM decided to call: {name}({args})")
            result_text = await mcp_client.call_tool(name, args)
            print(f"Tool result: {result_text}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result_text})

    conversation_memory.remember(messages[1:])
    return {"answer": "Sorry, I couldn't complete this request.", "tool_calls": tool_calls_made}