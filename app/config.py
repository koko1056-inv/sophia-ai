from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    app_title: str = "株式会社ソフィア AIチャットボット"
    embedding_model: str = "text-embedding-004"
    chat_model: str = "gemini-2.0-flash"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
