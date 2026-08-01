from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = ""
    provider_fallback_order: str = "yahoo,idx"
    provider_cache_ttl_hours: int = 24
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
