"""
Fernet symmetric encryption utilities for sensitive fields.

Used to encrypt/decrypt SUNAT credentials stored in the database.
The key is read from settings.SUNAT_FERNET_KEY (set via .env).

Usage:
    from common.encryption import encrypt, decrypt

    encrypted = encrypt("my-plain-password")  # → "gAAA..."
    plain = decrypt(encrypted)               # → "my-plain-password"

Key generation (run once):
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the configured key."""
    key = getattr(settings, "SUNAT_FERNET_KEY", "")
    if not key:
        raise ValueError(
            "SUNAT_FERNET_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plain_text: str) -> str:
    """Encrypt a plain-text string. Returns a Fernet token (base64 string)."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a Fernet token. Returns the original plain-text string."""
    if not token:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token — invalid key or corrupted data.")
        raise ValueError("No se pudo descifrar la credencial. La clave puede haber cambiado.")
