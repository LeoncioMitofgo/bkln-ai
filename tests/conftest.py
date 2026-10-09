import os
import sys
from pathlib import Path

# El código del backend importa `app.*`: los tests necesitan backend/ en el path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
os.environ.setdefault('GEMINI_API_KEY', 'test-key')
