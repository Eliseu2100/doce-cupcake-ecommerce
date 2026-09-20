"""
Camada Model — criptografia de dados sensíveis em repouso.

Telefone e endereço (rua, número, complemento, bairro, CEP) são
gravados criptografados no banco com Fernet (AES-128 em modo CBC +
HMAC, da biblioteca `cryptography`). Assim, se alguém copiar o
arquivo `cupcake.db` sem autorização, esses campos aparecem como
texto ilegível, não em claro.

A chave vem de `APP_ENCRYPTION_KEY` (variável de ambiente). Se não
estiver definida, derivamos uma chave a partir de SECRET_KEY só para
a aplicação não quebrar em desenvolvimento — mas isso NÃO é seguro
para produção: configure APP_ENCRYPTION_KEY de verdade (veja
DEPLOY.md). Cartão nunca passa por aqui porque o número completo e o
CVV simplesmente nunca são gravados no banco (só os 4 últimos
dígitos), então não há o que criptografar nesse caso.
"""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

_fernet_instance = None


def _build_fernet():
    key_source = current_app.config.get("APP_ENCRYPTION_KEY") or current_app.config["SECRET_KEY"]
    # Fernet exige uma chave de 32 bytes em base64 urlsafe. Derivamos
    # isso de qualquer string configurada via SHA-256, para não exigir
    # que a pessoa gere manualmente uma chave no formato exato do Fernet.
    digest = hashlib.sha256(key_source.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def _get_fernet():
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = _build_fernet()
    return _fernet_instance


def encrypt_field(value):
    """Criptografa uma string. None/"" continuam None/"" (não precisa
    criptografar campo vazio)."""
    if not value:
        return value
    token = _get_fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_field(token):
    """Descriptografa um campo. Se a chave mudou (ex.: alguém trocou
    APP_ENCRYPTION_KEY) ou o dado é anterior a essa camada, devolve um
    marcador em vez de quebrar a página inteira."""
    if not token:
        return token
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return "[dado protegido indisponível]"
