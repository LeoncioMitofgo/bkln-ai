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

La ingesta inicial se hará mediante `POST /sources/url` y `POST /sources/text`. En una siguiente fase añadiremos subida de PDF/DOCX y rastreo controlado de `bklnsoftware.tech`.

No guardes claves reales en Git ni las pegues en el chat.
