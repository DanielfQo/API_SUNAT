"""
Servicio de almacenamiento para guardar archivos en el sistema de archivos local.
"""
import os
from django.conf import settings

def save_file(company_dir: str, filename: str, content: bytes, folder: str) -> str:
    """
    Guarda un archivo en la carpeta especificada dentro del directorio de la empresa.
    Retorna la ruta relativa al archivo.
    """
    # Construir ruta de directorio absoluta: MEDIA_ROOT / company_dir / folder
    dir_path = os.path.join(settings.MEDIA_ROOT, company_dir, folder)
    
    # Crear directorios si no existen
    os.makedirs(dir_path, exist_ok=True)
    
    # Ruta absoluta al archivo
    file_path = os.path.join(dir_path, filename)
    
    # Guardar el archivo
    with open(file_path, 'wb') as f:
        f.write(content)
        
    # Retorna la ruta relativa para persistencia en base de datos (ej., "company_dir/xml/20123456789-01-F001-1.xml")
    return os.path.join(company_dir, folder, filename).replace('\\', '/')
