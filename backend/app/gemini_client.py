from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings

# Gemini devuelve a veces errores temporales de saturación: un reintento rápido en el
# mismo modelo. El 429 (sin cuota) no se reintenta aquí: main.py pasa al modelo siguiente.
RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=2,
    initial_delay=1.0,
    max_delay=4.0,
    http_status_codes=[408, 500, 502, 503, 504],
)


@lru_cache
def get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=get_settings().gemini_api_key,
        http_options=types.HttpOptions(retry_options=RETRY_OPTIONS),
    )
