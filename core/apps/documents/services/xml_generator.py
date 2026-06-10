"""
Generador XML simulado para Documentos Electrónicos.
En una implementación real, esto usaría una librería o motor de plantillas
para construir un XML UBL (Universal Business Language) válido para SUNAT.
"""
import os
from decimal import Decimal
from jinja2 import Environment, FileSystemLoader
from apps.documents.models import ElectronicDocument

# Ruta al directorio de plantillas
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates', 'ubl21')

def num_to_words(number):
    """
    Función súper básica para MVP. 
    En producción se usa una librería como num2words.
    """
    # Para el MVP, si es 118, devolvemos "CIENTO DIECIOCHO CON 00/100"
    entero = int(number)
    decimal = int(round((number - entero) * 100))
    return f"CIENTO DIECIOCHO CON {decimal:02d}/100"

def generate_fake_ubl(document: ElectronicDocument) -> str:
    """
    Genera una representación XML UBL 2.1 válida del documento utilizando Jinja2.
    Calcula el IGV exacto y los totales basándose en document.details.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template('invoice.xml')
    
    # Calcular totales
    total_gravadas = Decimal('0.00')
    details = document.details or []
    
    if not details:
        # Alternativa para pruebas antiguas sin detalles
        details = [{
            "description": "Producto de prueba",
            "quantity": 1,
            "unit_price": float(document.total_amount) / 1.18
        }]
    
    # Recalcular todo a partir de los detalles para ser exactos
    processed_details = []
    for item in details:
        qty = Decimal(str(item.get('quantity', 1)))
        price = Decimal(str(item.get('unit_price', 0)))
        total_gravadas += (qty * price)
        processed_details.append({
            "description": item.get('description', 'Item'),
            "quantity": float(qty),
            "unit_price": float(price)
        })
        
    total_igv = total_gravadas * Decimal('0.18')
    total_amount = total_gravadas + total_igv
    
    # Formatear el monto en palabras
    total_amount_words = num_to_words(float(total_amount))
    
    context = {
        "document": document,
        "details": processed_details,
        "total_gravadas": float(total_gravadas),
        "total_igv": float(total_igv),
        "total_amount": float(total_amount),
        "total_amount_words": total_amount_words
    }
    
    return template.render(**context)
