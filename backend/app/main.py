import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types

from app.config import get_settings
from app.embeddings import embed_text
from app.gemini_client import get_gemini_client
from app.models import ChatRequest, ChatResponse, HealthResponse, SourceRequest, UrlSourceRequest
from app.supabase_client import get_supabase

logger = logging.getLogger(__name__)
app = FastAPI(title='BKLN AI', version='0.1.0')
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


@app.get('/health', response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        get_supabase().table('sources').select('id').limit(1).execute()
        supabase_connected = True
    except Exception:
        supabase_connected = False
    return HealthResponse(
        status='ok' if supabase_connected else 'degraded',
        supabase_connected=supabase_connected,
        gemini_configured=bool(settings.gemini_api_key),
    )


@app.post('/sources/text')
def add_text_source(payload: SourceRequest) -> dict[str, str]:
    try:
        embedding = embed_text(payload.content)
        response = get_supabase().table('sources').insert({
            'title': payload.title,
            'content': payload.content,
            'source_url': payload.source_url,
            'embedding': embedding,
        }).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail='No se pudo guardar la fuente') from exc
    return {'id': str(response.data[0]['id'])}


@app.post('/sources/url')
def add_url_source(payload: UrlSourceRequest) -> dict[str, str]:
    raise HTTPException(status_code=501, detail='La ingesta web se implementará en la siguiente fase')


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        query_embedding = embed_text(payload.question)
        result = get_supabase().rpc('search_sources', {
            'query_embedding': query_embedding,
            'match_limit': 6,
        }).execute()
        matches = [
            item for item in (result.data or [])
            if float(item.get('similarity', 0)) >= settings.chat_min_context_score
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail='No se pudo consultar la base de conocimiento') from exc

    if not matches:
        return ChatResponse(
            answer='No encuentro información suficiente en la base de conocimiento de BKLN para responder a eso.',
            sources=[],
            grounded=False,
        )

    context = '\n\n'.join(
        f"Fuente: {item.get('title', 'Sin título')}\n{item.get('content', '')}"
        for item in matches
    )
    prompt = (
        'Responde únicamente usando el contexto proporcionado. Si la respuesta no está en el contexto, '
        'di claramente que no tienes información suficiente. No inventes precios, fechas, funcionalidades '
        'ni promesas. Responde en español y sé conciso.\n\n'
        f'CONTEXTO:\n{context}\n\nPREGUNTA:\n{payload.question}'
    )
    try:
        response = get_gemini_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
    except Exception as exc:
        logger.exception('Gemini generation failed')
        detail = 'No se pudo consultar Gemini'
        if settings.environment == 'development':
            detail = f'Gemini error: {exc}'
        raise HTTPException(status_code=502, detail=detail) from exc

    return ChatResponse(
        answer=response.text or 'No he podido generar una respuesta.',
        sources=[item.get('source_url') or item.get('title', 'Fuente BKLN') for item in matches],
        grounded=True,
    )
