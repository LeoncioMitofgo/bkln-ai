# Configuracion externa

## 1. Supabase

Crea un proyecto nuevo y abre el SQL Editor.

1. Ejecuta `supabase/schema.sql`.
2. Comprueba que existe la tabla `sources`.
3. Comprueba que la funcion `search_sources` aparece en Database > Functions.
4. Copia la URL del proyecto y la `service_role` key en tu gestor de secretos. No las pegues en el chat ni las subas a Git.

La `service_role` key solo debe vivir en el backend. Nunca debe llegar al navegador.

## 2. Gemini

1. Abre Google AI Studio.
2. Crea una API key nueva para este proyecto.
3. Guarda la key en un gestor de secretos.
4. No la incluyas en el frontend ni en Git.

El backend usa:

- Modelo de respuesta: `GEMINI_MODEL`.
- Modelo de embeddings: `GEMINI_EMBEDDING_MODEL`.

## 3. Configuracion local

Copia `backend/.env.example` a `backend/.env` y rellena:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
GEMINI_API_KEY=...
```

No necesitamos configurar todavia dominio, Railway, WhatsApp ni el widget del sitio. Primero validaremos la ingesta y las respuestas localmente.

## 4. Primera prueba

Cuando las variables esten configuradas:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

Comprueba:

- `GET http://localhost:8010/health`
- `POST http://localhost:8010/sources/text`
- `POST http://localhost:8010/chat`

## Pendiente despues de esta fase

- Rastreador de `https://www.bklnsoftware.tech`.
- Subida de PDF, DOCX y Markdown.
- Fragmentacion de documentos largos.
- Fuentes visibles en la respuesta.
- Widget propio para el sitio.
- Tests de grounding y prompt injection.
- Despliegue externo.
