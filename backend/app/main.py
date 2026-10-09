import logging
import secrets
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types

from app.config import get_settings
from app.embeddings import embed_text
from app.gemini_client import get_gemini_client
from app.models import ChatRequest, ChatResponse, ChatTurn, HealthResponse, SourceRequest, UrlSourceRequest
from app.prompts import BASE_CONTEXT_TITLES, SYSTEM_INSTRUCTION
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


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    # Sin ADMIN_TOKEN configurado la ingesta queda cerrada: nadie puede escribir en la base.
    expected = settings.admin_token
    if not expected or not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail='No autorizado')


@app.post('/sources/text', dependencies=[Depends(require_admin)])
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


@app.post('/sources/url', dependencies=[Depends(require_admin)])
def add_url_source(payload: UrlSourceRequest) -> dict[str, str]:
    raise HTTPException(status_code=501, detail='La ingesta web se implementará en la siguiente fase')


_BASE_CONTEXT_TTL = 600
_base_context_cache: tuple[float, list[dict]] = (0.0, [])


def get_base_context() -> list[dict]:
    """Entradas fijas (resumen de servicios, ficha, contacto), cacheadas unos minutos."""
    global _base_context_cache
    fetched_at, rows = _base_context_cache
    if rows and time.monotonic() - fetched_at < _BASE_CONTEXT_TTL:
        return rows
    try:
        result = (
            get_supabase()
            .table('sources')
            .select('title,content,source_url')
            .in_('title', list(BASE_CONTEXT_TITLES))
            .execute()
        )
        rows = result.data or []
    except Exception:
        logger.exception('No se pudo cargar el contexto base')
        rows = []
    _base_context_cache = (time.monotonic(), rows)
    return rows


def normalize_history(history: list[ChatTurn], max_turns: int) -> list[ChatTurn]:
    """Últimos turnos, empezando por el visitante y sin dos turnos seguidos del mismo rol."""
    turns: list[ChatTurn] = []
    for turn in history[-max_turns:]:
        if not turns and turn.role != 'user':
            continue
        if turns and turns[-1].role == turn.role:
            turns[-1] = ChatTurn(role=turn.role, content=turns[-1].content + '\n' + turn.content)
        else:
            turns.append(turn)
    # El mensaje actual del visitante va después: el historial tiene que acabar en el asistente.
    if turns and turns[-1].role == 'user':
        turns.pop()
    return turns


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    history = normalize_history(payload.history, settings.chat_history_turns)
    # Buscar también con lo último que dijo el visitante, para entender preguntas de seguimiento.
    recent_user = [t.content for t in history if t.role == 'user'][-2:]
    retrieval_query = '\n'.join([*recent_user, payload.question])
    try:
        query_embedding = embed_text(retrieval_query)
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

    matched_titles = {item.get('title') for item in matches}
    context_rows = matches + [row for row in get_base_context() if row.get('title') not in matched_titles]
    if not context_rows:
        return ChatResponse(
            answer='Ahora mismo no puedo consultar la información de BKLN. Escríbenos por WhatsApp '
                   '(https://wa.me/240222798086) o a hello@bklnsoftware.tech y te respondemos.',
            sources=[],
            grounded=False,
        )

    context = '\n\n'.join(
        f"Fuente: {item.get('title', 'Sin título')}\n{item.get('content', '')}"
        for item in context_rows
    )
    contents = [
        types.Content(role='user' if turn.role == 'user' else 'model', parts=[types.Part(text=turn.content)])
        for turn in history
    ]
    contents.append(types.Content(
        role='user',
        parts=[types.Part(text=f'CONTEXTO:\n{context}\n\nMENSAJE DEL VISITANTE:\n{payload.question}')],
    ))
    try:
        response = get_gemini_client().models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=settings.chat_temperature,
            ),
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
        grounded=bool(matches),
    )
