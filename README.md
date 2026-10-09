# BKLN AI

Asistente de conocimiento de BKLN basado en Gemini, Supabase y pgvector.

La primera versión responde únicamente con información indexada desde la web y archivos autorizados. Si no encuentra contexto suficiente, debe indicarlo en lugar de inventar una respuesta.

## Estructura

- `backend/`: API FastAPI y lógica RAG.
- `backend/app/`: configuración, proveedores, Supabase e ingesta.
- `supabase/schema.sql`: tablas, funciones y políticas iniciales.
- `tests/`: pruebas del backend.

## Desarrollo local

1. Copia `backend/.env.example` a `backend/.env`.
2. Rellena las variables de Supabase y Gemini.
3. Ejecuta `supabase/schema.sql` en el SQL Editor de Supabase.
4. Instala dependencias:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

5. Arranca la API:

```powershell
uvicorn app.main:app --reload --port 8010
```

6. Comprueba `http://localhost:8010/health`.

## Fuentes

La ingesta se hace mediante `POST /sources/text` (y, más adelante, `POST /sources/url`). En una siguiente fase añadiremos subida de PDF/DOCX y rastreo controlado de `bklnsoftware.tech`.

Los endpoints `/sources/*` exigen la cabecera `X-Admin-Token` con el valor de `ADMIN_TOKEN`. Si `ADMIN_TOKEN` no está configurado, la ingesta queda cerrada. `knowledge/ingest_to_backend.py` lee el token de `BKLN_AI_ADMIN_TOKEN` o, si no existe, de `backend/.env`.

No guardes claves reales en Git ni las pegues en el chat.

## Comportamiento del asistente

- Las instrucciones están en `backend/app/prompts.py`: orienta como un asesor (entiende el problema, propone servicio, producto o guía de la base, hace como mucho dos preguntas, no inventa precios ni plazos y cierra con WhatsApp o correo).
- Memoria: el widget de la web envía los últimos mensajes en `history`; el servidor no guarda conversaciones.
- Además de lo que encuentra la búsqueda, siempre añade al contexto las entradas de `BASE_CONTEXT_TITLES` (resumen de servicios, ficha y contacto), para poder orientar aunque no haya coincidencias.

## Tests

```powershell
backend\.venv\Scripts\python.exe -m pytest tests
```

Ejecútalos desde la raíz del repositorio para que no lean `backend/.env`.
