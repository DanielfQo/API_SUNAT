"""
Utilidades de cifrado simétrico Fernet para campos sensibles.

Utilizado para cifrar/descifrar las credenciales de SUNAT almacenadas en la base de datos.
La clave se lee desde settings.SUNAT_FERNET_KEY (establecida a través de .env).

Uso:
    from common.encryption import encrypt, decrypt

    encrypted = encrypt("my-plain-password")  # → "gAAA..."
    plain = decrypt(encrypted)               # → "my-plain-password"

Generación de clave (ejecutar una vez):
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Devuelve una instancia de Fernet utilizando la clave configurada."""
    key = getattr(settings, "SUNAT_FERNET_KEY", "")
    if not key:
        raise ValueError(
            "SUNAT_FERNET_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plain_text: str) -> str:
    """Cifra una cadena de texto plano. Devuelve un token Fernet (cadena base64)."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt(token: str) -> str:
    """Descifra un token Fernet. Devuelve la cadena de texto plano original."""
    if not token:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token — invalid key or corrupted data.")
        raise ValueError("No se pudo descifrar la credencial. La clave puede haber cambiado.")
