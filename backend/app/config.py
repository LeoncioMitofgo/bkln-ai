from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    supabase_url: str
    supabase_service_role_key: str
    gemini_api_key: str
    gemini_model: str = 'gemini-3.6-flash'
    gemini_embedding_model: str = 'gemini-embedding-001'
    environment: str = 'development'
    allowed_origins: str = 'http://localhost:3000'
    chat_min_context_score: float = 0.35

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
