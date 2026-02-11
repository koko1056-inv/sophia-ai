import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    app_title: str = "株式会社ソフィア AIチャットボット"
    knowledge_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "knowledge"
    )
    vectorstore_path: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "vectorstore"
    )
    faq_path: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "faq.json"
    )
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 3

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
