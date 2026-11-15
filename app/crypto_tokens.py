"""Cifra credenciais de contas usando a chave existente da instalação."""
import os

from cryptography.fernet import Fernet, InvalidToken

PREFIX = "ceq-enc:v1:"


class ErroChave(ValueError):
    """A chave ausente ou incorreta impede o acesso seguro à credencial."""


def _chave():
    key = os.environ.get("CEQ_ENCRYPTION_KEY", "")
    if not key:
        raise ErroChave("CEQ_ENCRYPTION_KEY ausente")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise ErroChave("CEQ_ENCRYPTION_KEY inválida") from exc


def cifrar(valor):
    if not isinstance(valor, str) or not valor:
        raise ValueError("Token vazio ou inválido")
    return PREFIX + _chave().encrypt(valor.encode()).decode()


def ler(valor):
    if not valor.startswith(PREFIX):
        return valor  # legado, somente leitura até migração explícita
    try:
        return _chave().decrypt(valor[len(PREFIX):].encode()).decode()
    except (InvalidToken, UnicodeError) as exc:
        raise ErroChave("Não foi possível decifrar o token com esta chave") from exc
