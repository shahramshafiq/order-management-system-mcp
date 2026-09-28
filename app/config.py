from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    guardrails_model: str = "gpt-4.1-mini"
    guardrails_config_path: str = "guardrails_config"

    products_file: str = "data/products.json"
    orders_file: str = "data/orders.json"
    suppliers_file: str = "data/suppliers.json"
    movements_file: str = "data/movements.json"
    idempotency_file: str = "data/idempotency_keys.json"

    currency: str = "PKR"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
