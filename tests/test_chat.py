from fastapi.testclient import TestClient

import app.main as main
from app.models import ChatRequest, ChatTurn

client = TestClient(main.app)
SOURCE = {'title': 'Prueba', 'content': 'Contenido de prueba'}


def test_sources_text_closed_without_admin_token_configured(monkeypatch):
    monkeypatch.setattr(main.settings, 'admin_token', '')
    response = client.post('/sources/text', json=SOURCE, headers={'X-Admin-Token': 'cualquiera'})
    assert response.status_code == 401


def test_sources_text_rejects_missing_or_wrong_token(monkeypatch):
    monkeypatch.setattr(main.settings, 'admin_token', 'secreto')
    assert client.post('/sources/text', json=SOURCE).status_code == 401
    assert client.post('/sources/text', json=SOURCE, headers={'X-Admin-Token': 'otro'}).status_code == 401


def test_sources_text_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(main.settings, 'admin_token', 'secreto')
    monkeypatch.setattr(main, 'embed_text', lambda text: [0.0])

    class FakeQuery:
        def insert(self, row):
            return self

        def execute(self):
            return type('Result', (), {'data': [{'id': 'abc'}]})()

    class FakeSupabase:
        def table(self, name):
            return FakeQuery()

    monkeypatch.setattr(main, 'get_supabase', lambda: FakeSupabase())
    response = client.post('/sources/text', json=SOURCE, headers={'X-Admin-Token': 'secreto'})
    assert response.status_code == 200
    assert response.json() == {'id': 'abc'}


def test_normalize_history_starts_with_user_and_ends_with_assistant():
    history = [
        ChatTurn(role='assistant', content='Hola, ¿en qué te ayudo?'),
        ChatTurn(role='user', content='Tengo una farmacia'),
        ChatTurn(role='user', content='y me faltan productos'),
        ChatTurn(role='assistant', content='¿Cuántas cajas tienes?'),
        ChatTurn(role='user', content='Dos'),
    ]
    turns = main.normalize_history(history, max_turns=8)
    assert [t.role for t in turns] == ['user', 'assistant']
    assert turns[0].content == 'Tengo una farmacia\ny me faltan productos'


def test_normalize_history_respects_max_turns():
    history = [ChatTurn(role='user' if i % 2 == 0 else 'assistant', content=str(i)) for i in range(12)]
    turns = main.normalize_history(history, max_turns=4)
    assert [t.content for t in turns] == ['8', '9', '10', '11']


def test_chat_request_history_is_optional():
    assert ChatRequest(question='Hola').history == []
