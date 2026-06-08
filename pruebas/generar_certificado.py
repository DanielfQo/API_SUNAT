from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from datetime import datetime, timedelta, timezone


# Configuracion
RUC = "10763375621"
RAZON_SOCIAL = "EMPRESA DE PRUEBA SAC"
PASSWORD = "123456"  # Esta sera la clave del .pfx


# 1. Generar llave privada
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)


# 2. Crear certificado autofirmado
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "PE"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, RAZON_SOCIAL),
    x509.NameAttribute(NameOID.COMMON_NAME, RUC),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(private_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(timezone.utc))
    .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    .sign(private_key, hashes.SHA256())
)


# 3. Guardar llave privada
with open("private.key", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
    )


# 4. Guardar certificado .crt
with open("certificado.crt", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))


# 5. Crear archivo .pfx / .p12
pfx_data = pkcs12.serialize_key_and_certificates(
    name=b"certificado_prueba",
    key=private_key,
    cert=cert,
    cas=None,
    encryption_algorithm=serialization.BestAvailableEncryption(PASSWORD.encode())
)

with open("certificado_prueba.pfx", "wb") as f:
    f.write(pfx_data)


print("Certificado generado correctamente.")
print("Archivos creados:")
print("- private.key")
print("- certificado.crt")
print("- certificado_prueba.pfx")
print()
print(f"Password del PFX: {PASSWORD}")