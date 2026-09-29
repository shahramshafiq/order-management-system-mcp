_session = None


def set_session(session):
    global _session
    _session = session


async def get_openai_tools() -> list[dict]:
    mcp_tools = await _session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in mcp_tools.tools
    ]


async def call_tool(name: str, args: dict) -> str:
    try:
        result = await _session.call_tool(name, args)
        if not result.content:
            return "[]"
        return "\n".join(block.text for block in result.content)
    except Exception as e:
        return f"Error calling {name}: {e}"