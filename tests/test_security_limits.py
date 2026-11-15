from starlette.requests import Request
from app import main


def test_webhook_rejeita_corpo_excessivo(client):
    r = client.post('/webhook', content=b'x' * (1024 * 1024 + 1))
    assert r.status_code == 413


def test_protocolo_encaminhado_de_cliente_externo_nao_e_confiavel(monkeypatch):
    monkeypatch.setattr(main, 'PERMITE_HTTP', False)
    monkeypatch.setattr(main, 'COOKIE_SEGURO', True)
    scope = {'type': 'http', 'method': 'POST', 'scheme': 'http', 'path': '/login',
             'server': ('example.com', 80), 'client': ('8.8.8.8', 1234),
             'headers': [(b'host', b'example.com'), (b'x-forwarded-proto', b'https')]}
    assert main.conexao_insegura(Request(scope))
