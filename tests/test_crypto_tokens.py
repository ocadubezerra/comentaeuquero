import uuid
import threading

import pytest
from cryptography.fernet import Fernet
from app import db, crypto_tokens, segredos, alerta


@pytest.fixture(autouse=True)
def banco_isolado(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "_local", threading.local())
    db.init()
    yield
    db.conn().close()


def test_tokens_cifrados_e_chave_obrigatoria(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CEQ_ENCRYPTION_KEY", key)
    account = db.upsert_account(uuid.uuid4().hex, "", "teste", "token-secreto", "")
    raw = db.conn().execute("SELECT access_token FROM accounts WHERE id=?", (account["id"],)).fetchone()[0]
    assert raw.startswith(crypto_tokens.PREFIX) and "token-secreto" not in raw
    assert db.get_account(account["id"])["access_token"] == "token-secreto"
    monkeypatch.setenv("CEQ_ENCRYPTION_KEY", Fernet.generate_key().decode())
    with pytest.raises(ValueError):
        db.get_account(account["id"])
    monkeypatch.delenv("CEQ_ENCRYPTION_KEY")
    with pytest.raises(ValueError):
        db.update_token(account["id"], "novo", "")
    with pytest.raises(ValueError):
        segredos.guardar("teste", "valor")
    db.delete_account(account["id"])


def test_migracao_atomica_de_legados(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CEQ_ENCRYPTION_KEY", key)
    c = db.conn()
    ident = uuid.uuid4().hex
    c.execute("INSERT INTO accounts(ig_id, access_token) VALUES (?, ?)", (ident, "legado"))
    c.execute("INSERT INTO ajustes(chave, valor) VALUES (?, ?)", ("seg:migracao_teste", "raw:segredo"))
    c.execute("INSERT INTO ajustes(chave, valor) VALUES (?, ?)", ("alerta_telegram_token", "token-telegram"))
    c.commit()
    assert db.migrar_credenciais()[0] >= 1
    raw = c.execute("SELECT access_token FROM accounts WHERE ig_id=?", (ident,)).fetchone()[0]
    assert raw.startswith(crypto_tokens.PREFIX)
    assert db.get_account_by_ig_id(ident)["access_token"] == "legado"
    assert segredos.ler("migracao_teste") == "segredo"
    assert db.get_ajuste("alerta_telegram_token", "").startswith(crypto_tokens.PREFIX)
    assert alerta.credenciais()[0] == "token-telegram"
    assert db.migrar_credenciais() == (0, 0)


def test_chave_trocada_nao_sobrescreve_e_migracao_nao_altera(monkeypatch):
    monkeypatch.setenv("CEQ_ENCRYPTION_KEY", Fernet.generate_key().decode())
    conta = db.upsert_account("conta-chave", "", "teste", "original", "")
    c = db.conn()
    c.execute("INSERT INTO accounts(ig_id, access_token) VALUES (?, ?)", ("legada", "texto-legado"))
    c.commit()
    monkeypatch.setenv("CEQ_ENCRYPTION_KEY", Fernet.generate_key().decode())
    with pytest.raises(ValueError):
        db.upsert_account("conta-chave", "", "teste", "substituto", "")
    with pytest.raises(ValueError):
        segredos.guardar("outro", "substituto")
    with pytest.raises(ValueError):
        db.migrar_credenciais()
    assert c.execute("SELECT access_token FROM accounts WHERE ig_id='legada'").fetchone()[0] == "texto-legado"
    assert c.execute("SELECT access_token FROM accounts WHERE id=?", (conta["id"],)).fetchone()[0].startswith(crypto_tokens.PREFIX)
