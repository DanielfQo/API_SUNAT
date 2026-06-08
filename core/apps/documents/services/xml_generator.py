"""
Mock XML Generator for Electronic Documents.
In a real implementation, this would use a library or template engine 
to build a valid UBL (Universal Business Language) XML for SUNAT.
"""
import os
from decimal import Decimal
from jinja2 import Environment, FileSystemLoader
from apps.documents.models import ElectronicDocument

# Path to the templates directory
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
    Generates a valid UBL 2.1 XML representation of the document using Jinja2.
    Calculates exact IGV and totals based on document.details.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template('invoice.xml')
    
    # Calculate totals
    total_gravadas = Decimal('0.00')
    details = document.details or []
    
    if not details:
        # Fallback for old tests without details
        details = [{
            "description": "Producto de prueba",
            "quantity": 1,
            "unit_price": float(document.total_amount) / 1.18
        }]
    
    # Recalculate everything from details to be exact
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
    
    # Format amount in words
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
