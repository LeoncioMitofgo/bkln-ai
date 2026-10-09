from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    supabase_url: str
    supabase_service_role_key: str
    gemini_api_key: str
    gemini_model: str = 'gemini-3.6-flash'
    # Si el modelo principal está saturado (5xx) o sin cuota (429), se prueban estos en orden.
    gemini_fallback_models: str = 'gemini-3.5-flash,gemini-3.7-flash,gemini-3.6-flash'
    gemini_embedding_model: str = 'gemini-embedding-001'
    environment: str = 'development'
    allowed_origins: str = 'http://localhost:3000'
    chat_min_context_score: float = 0.35
    # Mensajes previos de la conversación que se tienen en cuenta (los envía el widget).
    chat_history_turns: int = 8
    chat_temperature: float = 0.3
    # Token para los endpoints de ingesta (/sources/*). Si está vacío, la ingesta queda desactivada.
    admin_token: str = ''

    @property
    def chat_models(self) -> list[str]:
        models = [self.gemini_model, *self.gemini_fallback_models.split(',')]
        return list(dict.fromkeys(m.strip() for m in models if m.strip()))

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
