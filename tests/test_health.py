from fastapi.testclient import TestClient

from app.main import app


def test_health_shape():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert set(response.json()) == {'status', 'supabase_connected', 'gemini_configured'}
