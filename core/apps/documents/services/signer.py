import os
from lxml import etree
from signxml import XMLSigner, methods
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization

def load_certificate(pfx_path: str, password: str):
    """
    Carga el certificado PFX y extrae la llave privada y el certificado público.
    """
    if not os.path.exists(pfx_path):
        raise FileNotFoundError(f"El certificado {pfx_path} no existe.")
        
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    
    private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
        pfx_data, 
        password.encode('utf-8')
    )
    
    return private_key, cert

def sign_xml(xml_path: str, private_key, cert) -> str:
    """
    Firma digitalmente el XML usando el certificado y llave privada.
    Inserta la firma <ds:Signature> dentro del nodo <ext:ExtensionContent>.
    Sobreescribe el archivo original.
    """
    with open(xml_path, 'rb') as f:
        xml_data = f.read()
        
    root = etree.fromstring(xml_data)
    
    # 1. Sign the root document (enveloped)
    # Convert keys to PEM
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    
    signer = XMLSigner(
        method=methods.enveloped, 
        signature_algorithm='rsa-sha256', 
        digest_algorithm='sha256',
        c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
    )
    # exclude_c14n_transform_element=True evita que signxml agregue c14n al nodo Transforms (lo cual causa "Unknown transform algorithm" en SUNAT)
    signed_root = signer.sign(
        root, 
        key=priv_pem, 
        cert=cert_pem,
        exclude_c14n_transform_element=True
    )
    
    # 2. Guardar el XML firmado (signxml ya reemplazó el Id="placeholder" en su lugar)
    signed_xml_data = etree.tostring(signed_root, encoding='utf-8', xml_declaration=True)
    
    with open(xml_path, 'wb') as f:
        f.write(signed_xml_data)
        
    return xml_path
