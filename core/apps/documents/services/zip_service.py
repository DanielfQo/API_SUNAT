"""
Servicio Zip para comprimir archivos XML en memoria.
"""
import io
import zipfile

def compress_xml_to_zip(xml_content: str, xml_filename: str) -> bytes:
    """
    Comprime una cadena XML en un archivo ZIP en memoria.
    Devuelve el archivo ZIP como bytes.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_filename, xml_content.encode('utf-8'))
    return zip_buffer.getvalue()

def create_zip(xml_signed_path: str) -> bytes:
    """
    Lee un archivo XML (ya firmado) desde el disco y lo comprime.
    Retorna el ZIP en formato de bytes.
    """
    import os
    if not os.path.exists(xml_signed_path):
        raise FileNotFoundError(f"No se encontró el XML: {xml_signed_path}")
        
    filename = os.path.basename(xml_signed_path)
    
    with open(xml_signed_path, 'rb') as f:
        xml_data = f.read()
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(filename, xml_data)
        
    return zip_buffer.getvalue()


def compress_xml_bytes(xml_bytes: bytes, xml_filename: str) -> bytes:
    """
    Comprime bytes de XML en un archivo ZIP en memoria.
    Devuelve el archivo ZIP como bytes.
    """
    import io
    import zipfile
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(xml_filename, xml_bytes)
    return zip_buffer.getvalue()

