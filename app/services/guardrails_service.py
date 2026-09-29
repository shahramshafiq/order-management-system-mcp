from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import GenerationOptions

from app.config import settings

_config = RailsConfig.from_path(settings.guardrails_config_path)
_config.models[0].model = settings.guardrails_model
_rails = LLMRails(_config)


async def check_input(user_message: str) -> bool:
    """Returns True if the message is safe to process, False if it should be blocked."""
    result = await _rails.generate_async(
        messages=[{"role": "user", "content": user_message}],
        options=GenerationOptions(rails=["input"]),
    )
    return not bool(result.response)


async def check_output(user_message: str, bot_response: str) -> bool:
    """Returns True if the assistant's reply is safe to send, False if it should be blocked."""
    result = await _rails.generate_async(
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": bot_response},
        ],
        options=GenerationOptions(rails=["output"]),
    )
    return not bool(result.response)