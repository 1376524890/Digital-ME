from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://digital_me:digital_me_dev@localhost:5432/digital_me"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM (OpenAI-compatible)
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_max_tokens: int = 4096

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # App
    app_env: str = "development"
    log_level: str = "info"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
