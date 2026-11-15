"""Segredos que entram pelo painel. Cifrados com CEQ_ENCRYPTION_KEY (Fernet).

Sem chave válida, novas credenciais não são gravadas. Valores antigos em claro
continuam legíveis e são recifrados quando lidos com uma chave válida.
"""
import os

from . import db

def _fernet():
    """Fernet pronto, ou None sem chave. Levanta se a chave for inválida."""
    k = os.environ.get("CEQ_ENCRYPTION_KEY", "")
    if not k:
        return None
    from cryptography.fernet import Fernet
    return Fernet(k.encode())


def estado_chave() -> str:
    """'ok', 'ausente' ou 'invalida'."""
    if not os.environ.get("CEQ_ENCRYPTION_KEY", ""):
        return "ausente"
    try:
        _fernet()
    except Exception:
        return "invalida"
    return "ok"


def cifrado_disponivel() -> bool:
    return estado_chave() == "ok"


def _gravar(chave: str, valor: str) -> None:
    if not valor:
        db.set_ajuste(f"seg:{chave}", "")
        return
    if estado_chave() != "ok":
        raise ValueError("CEQ_ENCRYPTION_KEY ausente ou inválida; segredo não foi salvo")
    db.validar_chave_existente()
    db.set_ajuste(f"seg:{chave}", "enc:" + _fernet().encrypt(valor.encode()).decode())


def guardar(chave: str, valor: str) -> None:
    _gravar(chave, valor)


def ler(chave: str) -> str:
    bruto = db.get_ajuste(f"seg:{chave}", "")
    if not bruto:
        return ""
    if bruto.startswith("raw:"):
        valor = bruto[4:]
        # chave chegou depois do valor (instância que ganhou CEQ_ENCRYPTION_KEY):
        # aproveita a leitura pra tirar o valor do claro
        if valor and cifrado_disponivel():
            _gravar(chave, valor)
        return valor
    if not cifrado_disponivel():
        return ""
    try:
        return _fernet().decrypt(bruto[4:].encode()).decode()
    except Exception:
        return ""
