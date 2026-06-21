from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    step_delay_sec: float = 2.0
    database_url: str = "sqlite:///./data/gtm.db"

    class Config:
        env_file = ".env"


settings = Settings()
