import logging
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
from zeep.exceptions import Fault
import requests

import os

logger = logging.getLogger(__name__)

class SunatClient:
    """
    Cliente SOAP para comunicarse con los servicios de SUNAT.
    """
    # Endpoint BETA local file
    WSDL_PATH = os.path.join(os.path.dirname(__file__), "billService.wsdl")

    def __init__(self):
        # Credenciales fijas de prueba según requerimiento
        self.username = "1076337562MODDATOS"
        self.password = "MODDATOS"
        
        session = requests.Session()
        session.verify = False # Sometimes SUNAT BETA has SSL issues
        session.auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0'
        })
        transport = Transport(session=session)
        
        self.client = Client(
            wsdl=self.WSDL_PATH,
            wsse=UsernameToken(self.username, self.password),
            transport=transport
        )

    def send_bill(self, zip_bytes: bytes, filename: str) -> dict:
        """
        Envía el comprobante empaquetado en ZIP usando el método sendBill.
        
        Args:
            zip_bytes: El contenido del ZIP en bytes.
            filename: El nombre del archivo (ej. 20123456789-01-F001-1.zip).
            
        Returns:
            Un diccionario con el estado y la respuesta de SUNAT.
        """
        logger.info(f"Enviando {filename} a SUNAT BETA...")
        try:
            # Enviar la solicitud SOAP
            # Zeep convierte automáticamente los bytes a base64 porque el tipo WSDL es base64Binary
            response = self.client.service.sendBill(
                fileName=filename,
                contentFile=zip_bytes
            )
            
            # sendBill retorna los bytes del CDR (Constancia de Recepción) en caso de éxito.
            # En otros métodos como sendSummary retorna un ticket.
            # Convertimos la respuesta a un formato manejable para guardar en base de datos.
            
            is_bytes = isinstance(response, bytes)
            
            return {
                "success": True,
                "sunat_ticket": "CDR_RECEIVED" if is_bytes else str(response),
                "cdr_bytes": response if is_bytes else None,
                "raw_response": "CDR ZIP data" if is_bytes else str(response)
            }
            
        except Fault as fault:
            # Errores SOAP devueltos por SUNAT (ej. XML inválido, datos incorrectos)
            logger.error(f"Error SOAP de SUNAT: {fault.message}")
            return {
                "success": False,
                "error_code": str(fault.code)[:10] if fault.code else "FAULT",
                "error_message": fault.message,
                "raw_response": str(fault)
            }
        except Exception as e:
            # Otros errores de conexión
            logger.exception("Error de conexión al enviar a SUNAT")
            return {
                "success": False,
                "error_code": "CONN_ERR",
                "error_message": str(e),
                "raw_response": str(e)
            }
