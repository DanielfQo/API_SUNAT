"""
Servicio de orquestación de documentos.
Maneja el flujo completo de creación de un documento electrónico.
"""
import hashlib
import os
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.companies.models import Company
from apps.client_apps.models import ClientApp
from apps.documents.models import ElectronicDocument
from apps.requests_log.models import RequestLog
from apps.sunat.services.status_checker import get_status

from .xml_generator import generate_fake_ubl
from .storage_service import save_file
from .zip_service import create_zip
from .signer import load_certificate, sign_xml
import re
from apps.sunat.services.client import SunatClient

def get_company_dir_name(company) -> str:
    """
    Returns a sanitized name of the company to use as a directory name.
    If the business name becomes empty after sanitization, falls back to RUC.
    """
    name = company.business_name
    # Remove characters that aren't alphanumeric, spaces, hyphens, or underscores
    cleaned = re.sub(r'[^\w\s-]', '', name).strip()
    # Replace spaces/hyphens with underscores
    cleaned = re.sub(r'[\s-]+', '_', cleaned)
    # Convert to lowercase
    cleaned = cleaned.lower()
    if not cleaned:
        return company.ruc
    return cleaned

def create_document(company: Company, client_app: ClientApp, data: dict, idempotency_key: str = None) -> tuple[ElectronicDocument, bool]:
    """
    Crea un documento y ejecuta el flujo de generación:
    1. Crea el registro en DB (PENDING)
    2. Genera el XML
    3. Guarda el XML
    4. Firma el XML
    5. Comprime el XML firmado a ZIP
    6. Guarda el ZIP
    7. Envía a SUNAT BETA
    8. Registra en RequestLog
    9. Actualiza el registro en DB (SENT)
    """
    series = data.get('series')
    number = data.get('number')
    
    # Paso 0: Validar clave de idempotencia
    if idempotency_key:
        existing = ElectronicDocument.objects.filter(company=company, idempotency_key=idempotency_key).first()
        if existing:
            import json
            from django.core.serializers.json import DjangoJSONEncoder
            
            safe_payload = json.loads(
                json.dumps({"idempotency_key": idempotency_key, "data": data}, cls=DjangoJSONEncoder)
            )
            
            # Registrar RequestLog: operación = IDEMPOTENCY_HIT
            RequestLog.objects.create(
                company=company,
                client_app=client_app,
                electronic_document=existing,
                operation=RequestLog.Operation.IDEMPOTENCY_HIT,
                request_payload=safe_payload,
                response_payload={"id": str(existing.id), "status": existing.sunat_status},
                status=RequestLog.Status.SUCCESS
            )
            return existing, True

    # Paso 1: Crear el documento en una transacción
    with transaction.atomic():
        if ElectronicDocument.objects.filter(company=company, series=series, number=number).exists():
            raise ValidationError(f"Document {series}-{number} already exists for this company.")
            
        document = ElectronicDocument.objects.create(
            company=company,
            document_type=data.get('document_type'),
            series=series,
            number=number,
            customer_document_type=data.get('customer_document_type', ''),
            customer_document=data.get('customer_document'),
            customer_name=data.get('customer_name', ''),
            total_amount=data.get('total_amount'),
            currency=data.get('currency', 'PEN'),
            sunat_status=ElectronicDocument.SunatStatus.PENDING,
            idempotency_key=idempotency_key
        )
    
    company_dir = get_company_dir_name(company)
    
    # Prefijo común de archivos: RUC-TIPO-SERIE-NUMERO
    file_prefix = f"{company.ruc}-{document.document_type}-{document.series}-{document.number}"
    xml_filename = f"{file_prefix}.xml"
    zip_filename = f"{file_prefix}.zip"

    # Paso 2: Generar XML
    xml_content = generate_fake_ubl(document)
    
    # Paso 3: Guardar XML (temporalmente sin firmar, o directamente firmado)
    xml_rel_path = save_file(company_dir, xml_filename, xml_content.encode('utf-8'), 'xml')
    xml_abs_path = os.path.join(settings.MEDIA_ROOT, xml_rel_path)
    
    # Paso 4: Firmar XML
    # Cargar certificado
    cert_path = os.path.join(settings.BASE_DIR, 'certs', 'certificado.pfx')
    private_key, cert = load_certificate(cert_path, "123456")
    # Firmar (sobreescribe el archivo)
    sign_xml(xml_abs_path, private_key, cert)
    
    # Paso 5: Comprimir XML firmado
    zip_content = create_zip(xml_abs_path)
    
    # Generar hash a partir del ZIP final o XML firmado
    with open(xml_abs_path, 'rb') as f:
        document_hash = hashlib.sha256(f.read()).hexdigest()

    # Paso 6: Guardar ZIP
    zip_rel_path = save_file(company_dir, zip_filename, zip_content, 'zip')
    
    # Actualizar estado a SIGNED antes de enviar (si algo falla, quedará como SIGNED)
    document.xml_path = xml_rel_path
    document.zip_path = zip_rel_path
    document.hash = document_hash
    document.sunat_status = ElectronicDocument.SunatStatus.SIGNED
    document.save(update_fields=['xml_path', 'zip_path', 'hash', 'sunat_status', 'updated_at'])
    
    # Paso 7: Enviar a SUNAT
    sunat_client = SunatClient()
    result = sunat_client.send_bill(zip_content, zip_filename)
    
    # Paso 8: Registrar solicitud
    RequestLog.objects.create(
        company=company,
        client_app=client_app,
        electronic_document=document,
        operation=RequestLog.Operation.SEND_INVOICE,
        request_payload={"filename": zip_filename, "size": len(zip_content)},
        response_payload={"raw": result.get("raw_response")},
        status=RequestLog.Status.SUCCESS if result.get("success") else RequestLog.Status.FAILED,
        error_message=result.get("error_message", "")
    )
    
    # Paso 9: Actualizar DB
    if result.get("success"):
        document.sunat_ticket = result.get("sunat_ticket", "")
        document.sunat_status = ElectronicDocument.SunatStatus.SENT
        document.sunat_response = {"raw": result.get("raw_response")}
        
        # Guardar CDR si existe
        if result.get("cdr_bytes"):
            cdr_filename = f"R-{zip_filename}"
            cdr_rel_path = save_file(company_dir, cdr_filename, result.get("cdr_bytes"), 'cdr')
            document.cdr_zip_path = cdr_rel_path
            
        document.save(update_fields=['sunat_status', 'sunat_ticket', 'sunat_response', 'cdr_zip_path', 'updated_at'])
    else:
        document.sunat_status = ElectronicDocument.SunatStatus.ERROR
        document.sunat_response_code = result.get("error_code", "")
        document.sunat_response = {"error": result.get("error_message")}
        document.save(update_fields=['sunat_status', 'sunat_response_code', 'sunat_response', 'updated_at'])
    
    return document, False


def check_status(document_id: str) -> ElectronicDocument:
    """
    Consulta el estado de un documento electrónico usando el ticket almacenado de SUNAT,
    actualiza el estado del documento, código de respuesta, descripción e historial de la solicitud.
    """
    try:
        document = ElectronicDocument.objects.select_related("company").get(id=document_id)
    except ElectronicDocument.DoesNotExist:
        raise ValidationError(f"Document with ID {document_id} does not exist.")
        
    company_dir = get_company_dir_name(document.company)
    ticket = document.sunat_ticket
    
    # Consultar SUNAT
    result = get_status(ticket)
    
    # Buscar client_app para el historial de auditoría de la solicitud
    previous_log = RequestLog.objects.filter(electronic_document=document, operation=RequestLog.Operation.SEND_INVOICE).first()
    client_app = previous_log.client_app if previous_log else ClientApp.objects.filter(company=document.company).first()
    
    # Registrar la operación de solicitud
    RequestLog.objects.create(
        company=document.company,
        client_app=client_app,
        electronic_document=document,
        operation=RequestLog.Operation.GET_STATUS,
        request_payload=result.get("raw_request"),
        response_payload={"raw": result.get("raw_response")},
        status=RequestLog.Status.SUCCESS if result.get("success") else RequestLog.Status.FAILED,
        error_message=result.get("error_message", "")
    )
    
    if result.get("success"):
        status_code = result.get("status_code", "")
        document.sunat_response_code = status_code
        document.sunat_response = {"raw": result.get("raw_response")}
        
        # Mapeo:
        # respuesta exitosa (código "0") -> ACCEPTED
        # respuesta de rechazo (código "99") -> REJECTED
        # en proceso (código "98") -> SENT (sin cambios de estado final, o según el código)
        if status_code == "0":
            document.sunat_status = ElectronicDocument.SunatStatus.ACCEPTED
            document.sunat_description = "Aceptado"
        elif status_code == "99":
            document.sunat_status = ElectronicDocument.SunatStatus.REJECTED
            document.sunat_description = "Rechazado"
        elif status_code == "98":
            document.sunat_status = ElectronicDocument.SunatStatus.SENT
            document.sunat_description = "En proceso"
        else:
            # Cualquier otro código
            document.sunat_status = ElectronicDocument.SunatStatus.ERROR
            document.sunat_description = f"Respuesta SUNAT con código desconocido: {status_code}"
            
        # Guardar CDR si existe
        cdr_bytes = result.get("content")
        if cdr_bytes:
            file_prefix = f"{document.company.ruc}-{document.document_type}-{document.series}-{document.number}"
            cdr_filename = f"R-{file_prefix}.zip"
            cdr_rel_path = save_file(company_dir, cdr_filename, cdr_bytes, 'cdr')
            document.cdr_zip_path = cdr_rel_path
    else:
        # Excepción o error de comunicación
        document.sunat_status = ElectronicDocument.SunatStatus.ERROR
        document.sunat_response_code = result.get("status_code", "ERROR")
        document.sunat_description = result.get("error_message", "Error al consultar estado en SUNAT")
        document.sunat_response = {"error": result.get("error_message")}
        
    document.save(update_fields=['sunat_status', 'sunat_response_code', 'sunat_description', 'sunat_response', 'cdr_zip_path', 'updated_at'])
    return document
