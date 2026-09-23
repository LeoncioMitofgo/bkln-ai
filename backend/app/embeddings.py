from app.config import get_settings
from app.gemini_client import get_gemini_client


def embed_text(text: str) -> list[float]:
    response = get_gemini_client().models.embed_content(
        model=get_settings().gemini_embedding_model,
        contents=text,
    )
    if not response.embeddings:
        raise RuntimeError('Gemini no devolvio un embedding')
    return list(response.embeddings[0].values)
