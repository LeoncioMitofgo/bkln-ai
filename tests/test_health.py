import os

os.environ.setdefault('SUPABASE_URL', 'https://example.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
os.environ.setdefault('GEMINI_API_KEY', 'test-key')

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_shape():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert set(response.json()) == {'status', 'supabase_connected', 'gemini_configured'}
