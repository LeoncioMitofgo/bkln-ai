from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings

# Gemini devuelve a veces errores temporales (saturación, límite de peticiones):
# se reintenta con espera creciente antes de dar el error al visitante.
RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=3,
    initial_delay=1.0,
    max_delay=8.0,
    http_status_codes=[408, 429, 500, 502, 503, 504],
)


@lru_cache
def get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=get_settings().gemini_api_key,
        http_options=types.HttpOptions(retry_options=RETRY_OPTIONS),
    )
