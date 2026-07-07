"""
Servicio de almacenamiento para guardar archivos en el sistema de almacenamiento configurado (Local o S3).
"""
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def save_file(company_dir: str, filename: str, content: bytes, folder: str) -> str:
    """
    Guarda un archivo en la carpeta especificada dentro del directorio de la empresa usando default_storage.
    Retorna la ruta relativa del archivo.
    """
    # Construir ruta relativa
    relative_path = f"{company_dir}/{folder}/{filename}".replace('\\', '/')
    
    # Si el archivo ya existe, eliminarlo para evitar que Django agregue un sufijo aleatorio
    if default_storage.exists(relative_path):
        default_storage.delete(relative_path)
        
    # Guardar usando el storage por defecto
    default_storage.save(relative_path, ContentFile(content))
        
    return relative_path

