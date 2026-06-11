import logging
from zeep.exceptions import Fault
from apps.sunat.services.client import SunatClient

logger = logging.getLogger(__name__)

def get_status(company, ticket: str) -> dict:
    """
    Consulta el estado de un ticket de SUNAT utilizando el cliente SOAP existente.
    
    Args:
        company: Instancia de la empresa (Company).
        ticket: El número de ticket de SUNAT (string).
        
    Returns:
        dict: Un diccionario de resultado con el estado de éxito, código de estado (status_code),
              contenido (bytes de la CDR) y detalles crudos de la solicitud/respuesta.
    """
    logger.info(f"Querying SUNAT status for ticket: {ticket} for company {company.ruc if company else 'None'}")
    sunat_client = SunatClient(company)

    
    try:
        # Llamar a la operación SOAP 'getStatus' definida en el WSDL
        response = sunat_client.client.service.getStatus(ticket=ticket)
        
        # Las respuestas de Zeep a veces pueden ser tipo diccionario u objetos según la configuración.
        # Manejamos ambos de forma segura.
        status_data = response.get("status") if isinstance(response, dict) else getattr(response, "status", None)
        
        if status_data is None:
            return {
                "success": False,
                "status_code": "NO_STATUS",
                "content": None,
                "error_message": "Response did not contain status information.",
                "raw_request": {"ticket": ticket},
                "raw_response": str(response)
            }
            
        status_code = status_data.get("statusCode") if isinstance(status_data, dict) else getattr(status_data, "statusCode", "")
        content = status_data.get("content") if isinstance(status_data, dict) else getattr(status_data, "content", None)
        
        return {
            "success": True,
            "status_code": status_code,
            "content": content,
            "error_message": "",
            "raw_request": {"ticket": ticket},
            "raw_response": f"statusCode: {status_code}, content: {'[bytes]' if content else 'None'}"
        }
        
    except Fault as fault:
        logger.error(f"SOAP Fault when querying ticket {ticket}: {fault.message}")
        return {
            "success": False,
            "status_code": str(fault.code)[:10] if fault.code else "FAULT",
            "content": None,
            "error_message": fault.message,
            "raw_request": {"ticket": ticket},
            "raw_response": str(fault)
        }
    except Exception as e:
        logger.exception(f"Connection error when querying ticket {ticket}")
        return {
            "success": False,
            "status_code": "CONN_ERR",
            "content": None,
            "error_message": str(e),
            "raw_request": {"ticket": ticket},
            "raw_response": str(e)
        }
