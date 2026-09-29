from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str
    openai_base_url: str

    guardrails_model: str
    guardrails_config_path: str = "guardrails_config"

    products_file: str = "data/products.json"
    orders_file: str = "data/orders.json"
    suppliers_file: str = "data/suppliers.json"
    movements_file: str = "data/movements.json"
    idempotency_file: str = "data/idempotency_keys.json"

    currency: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)