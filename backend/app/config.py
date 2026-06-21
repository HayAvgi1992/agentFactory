from pathlib import Path

from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    step_delay_sec: float = 2.0
    database_url: str = "sqlite:///./data/gtm.db"
    knowledge_dir: str = str(_PROJECT_ROOT / "knowledge")
    chroma_dir: str = str(_PROJECT_ROOT / "backend" / "data" / "chroma")
    rag_enabled: bool = True
    embedding_model: str = "text-embedding-3-small"
    default_prompt_version: str = "v1"

    class Config:
        env_file = ".env"


settings = Settings()
