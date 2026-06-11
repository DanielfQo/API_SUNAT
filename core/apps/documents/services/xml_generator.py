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
    Convierte un número a letras en español para comprobantes electrónicos.
    """
    UNIDADES = {
        0: 'CERO', 1: 'UN', 2: 'DOS', 3: 'TRES', 4: 'CUATRO', 5: 'CINCO',
        6: 'SEIS', 7: 'SIETE', 8: 'OCHO', 9: 'NUEVE', 10: 'DIEZ',
        11: 'ONCE', 12: 'DOCE', 13: 'TRECE', 14: 'CATORCE', 15: 'QUINCE',
        20: 'VEINTE', 30: 'TREINTA', 40: 'CUARENTA', 50: 'CINCUENTA',
        60: 'SESENTA', 70: 'SETENTA', 80: 'OCHENTA', 90: 'NOVENTA',
        100: 'CIEN'
    }
    
    # Especiales de decenas
    for i in range(16, 20):
        UNIDADES[i] = 'DIECI' + UNIDADES[i - 10]
    for i in range(21, 30):
        UNIDADES[i] = 'VEINTI' + UNIDADES[i - 20]

    def decenas(n):
        if n in UNIDADES:
            return UNIDADES[n]
        d = (n // 10) * 10
        u = n % 10
        return f"{UNIDADES[d]} Y {UNIDADES[u]}"

    def centenas(n):
        if n == 100:
            return 'CIEN'
        if n < 100:
            return decenas(n)
        c = n // 100
        resto = n % 100
        if c == 1:
            prefix = 'CIENTO'
        elif c == 5:
            prefix = 'QUINIENTOS'
        elif c == 7:
            prefix = 'SETECIENTOS'
        elif c == 9:
            prefix = 'NOVECIENTOS'
        else:
            prefix = UNIDADES[c] + 'CIENTOS'
            
        if resto == 0:
            return prefix
        return f"{prefix} {decenas(resto)}"

    def miles(n):
        if n < 1000:
            return centenas(n)
        m = n // 1000
        resto = n % 1000
        
        prefix = 'MIL' if m == 1 else f"{centenas(m)} MIL"
        if resto == 0:
            return prefix
        return f"{prefix} {centenas(resto)}"

    # Convertir monto
    entero = int(number)
    decimal = int(round((number - entero) * 100))
    
    if entero == 0:
        words = 'CERO'
    else:
        words = miles(entero)
        
    return f"{words} CON {decimal:02d}/100"


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
