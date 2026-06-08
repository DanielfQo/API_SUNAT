"""
Módulo para firma digital y envío a SUNAT
"""

import base64
import requests
from pathlib import Path
from typing import Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree


class FirmaService:
    """Servicio para firmar XML con certificado digital"""
    
    @staticmethod
    def firmar_xml(
        xml_path: Path,
        pfx_path: Path,
        pfx_password: str
    ) -> bool:
        """
        Firma un archivo XML usando un certificado PFX/P12.
        La firma se coloca dentro de ext:ExtensionContent.
        
        Args:
            xml_path: Ruta al archivo XML
            pfx_path: Ruta al certificado PFX/P12
            pfx_password: Contraseña del certificado
            
        Returns:
            bool: True si la firma fue exitosa
            
        Raises:
            FileNotFoundError: Si no encuentra el XML o certificado
            RuntimeError: Si hay error en la firma
        """
        try:
            from signxml import XMLSigner, methods
            from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            raise RuntimeError(
                "Faltan dependencias. Instala con:\n"
                "pip install lxml signxml cryptography zeep requests"
            )
        
        # Validar archivos
        if not xml_path.exists():
            raise FileNotFoundError(f"No existe el XML: {xml_path}")
        if not pfx_path.exists():
            raise FileNotFoundError(f"No existe el certificado: {pfx_path}")
        
        # Cargar certificado
        with open(pfx_path, "rb") as f:
            pfx_data = f.read()
        
        private_key, certificate, _ = load_key_and_certificates(
            pfx_data,
            pfx_password.encode("utf-8")
        )
        
        if private_key is None or certificate is None:
            raise RuntimeError("No se pudo leer la llave privada o el certificado desde el PFX/P12")
        
        # Convertir a PEM
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        cert_pem = certificate.public_bytes(
            encoding=serialization.Encoding.PEM
        )
        
        # Parsear XML
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(str(xml_path), parser).getroot()
        
        # Firmar
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        
        signed_root = signer.sign(
            root,
            key=key_pem,
            cert=cert_pem,
            reference_uri=None,
            id_attribute=None
        )
        
        # Mover firma a ExtensionContent
        ns = {
            "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
            "ds": "http://www.w3.org/2000/09/xmldsig#"
        }
        
        signature = signed_root.find(".//ds:Signature", namespaces=ns)
        extension_content = signed_root.find(
            ".//ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent",
            namespaces=ns
        )
        
        if signature is None:
            raise RuntimeError("No se generó la firma XMLDSig")
        
        if extension_content is None:
            raise RuntimeError("No se encontró ext:ExtensionContent para insertar la firma")
        
        # Remover firma del lugar anterior y agregarla a ExtensionContent
        parent = signature.getparent()
        if parent is not None:
            parent.remove(signature)
        
        extension_content.append(signature)
        
        # Guardar XML firmado
        tree = etree.ElementTree(signed_root)
        tree.write(
            str(xml_path),
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=False
        )
        
        return True


class ZipService:
    """Servicio para crear archivos ZIP"""
    
    @staticmethod
    def crear_zip(
        xml_path: Path,
        output_dir: Path,
        nombre_base: str
    ) -> Path:
        """
        Crea un archivo ZIP con el XML.
        
        Args:
            xml_path: Ruta al archivo XML
            output_dir: Directorio de salida
            nombre_base: Nombre base para el ZIP (sin extensión)
            
        Returns:
            Path: Ruta al archivo ZIP creado
        """
        output_dir.mkdir(exist_ok=True)
        
        zip_name = f"{nombre_base}.zip"
        zip_path = output_dir / zip_name
        
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
            zip_file.write(xml_path, arcname=xml_path.name)
        
        return zip_path


class SunatService:
    """Servicio para enviar comprobantes a SUNAT"""
    
    AMBIENTES = {
        "beta": "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService",
        "produccion": "https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService"
    }
    
    def __init__(
        self,
        usuario_sol: str,
        clave_sol: str,
        ambiente: str = "beta"
    ):
        """
        Inicializa el servicio SUNAT.
        
        Args:
            usuario_sol: Usuario SOL (RUC + "MODDATOS" para BETA)
            clave_sol: Contraseña SOL ("moddatos" para BETA)
            ambiente: 'beta' o 'produccion'
        """
        self.usuario_sol = usuario_sol
        self.clave_sol = clave_sol
        self.ambiente = ambiente
        self.url = self.AMBIENTES.get(ambiente)
        
        if not self.url:
            raise ValueError(f"Ambiente desconocido: {ambiente}. Use 'beta' o 'produccion'")
    
    def enviar_comprobante(
        self,
        zip_path: Path,
        zip_nombre: str,
        output_dir: Path = None
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Envía un comprobante a SUNAT y procesa la respuesta.
        
        Args:
            zip_path: Ruta al archivo ZIP
            zip_nombre: Nombre del archivo ZIP
            output_dir: Directorio para guardar CDR (default: mismo del ZIP)
            
        Returns:
            Tuple[bool, Optional[str], Optional[Path]]: 
                (éxito, mensaje, ruta_cdr_o_error)
        """
        if not zip_path.exists():
            return False, f"No existe el ZIP: {zip_path}", None
        
        if output_dir is None:
            output_dir = zip_path.parent
        
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Leer ZIP
            zip_base64 = base64.b64encode(zip_path.read_bytes()).decode("utf-8")
            
            # Preparar SOAP
            soap_xml = self._preparar_soap(zip_nombre, zip_base64)
            
            # Enviar
            print(f"[INFO] Enviando a SUNAT ({self.ambiente})...")
            response = requests.post(
                self.url,
                data=soap_xml.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "urn:sendBill"
                },
                timeout=60
            )
            
            print(f"[INFO] HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                return False, f"Error HTTP {response.status_code}", None
            
            # Procesar respuesta
            return self._procesar_respuesta(response, zip_nombre, output_dir)
        
        except Exception as e:
            return False, f"Error al enviar: {str(e)}", None
    
    def _preparar_soap(self, zip_nombre: str, zip_base64: str) -> str:
        """Prepara el XML SOAP para envío"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:ser="http://service.sunat.gob.pe"
                  xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soapenv:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>{self.usuario_sol}</wsse:Username>
                <wsse:Password>{self.clave_sol}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <ser:sendBill>
            <fileName>{zip_nombre}</fileName>
            <contentFile>{zip_base64}</contentFile>
        </ser:sendBill>
    </soapenv:Body>
</soapenv:Envelope>'''
    
    def _procesar_respuesta(
        self,
        response: requests.Response,
        zip_nombre: str,
        output_dir: Path
    ) -> Tuple[bool, str, Optional[Path]]:
        """Procesa la respuesta de SUNAT"""
        try:
            root = etree.fromstring(response.content)
            
            # Buscar error SOAP
            fault = root.find(".//faultstring")
            if fault is not None:
                return False, f"Error SOAP: {fault.text}", None
            
            # Buscar CDR
            app_response = root.find(".//applicationResponse")
            if app_response is None:
                return False, "applicationResponse no encontrado en respuesta", None
            
            # Decodificar CDR
            cdr_base64 = app_response.text
            cdr_bytes = base64.b64decode(cdr_base64)
            
            # Guardar CDR
            cdr_name = f"R-{zip_nombre}"
            cdr_path = output_dir / cdr_name
            cdr_path.write_bytes(cdr_bytes)
            
            print(f"[OK] CDR guardado: {cdr_path}")
            
            # Extraer CDR
            self._extraer_cdr(cdr_path, output_dir)
            
            return True, f"Comprobante enviado exitosamente. CDR: {cdr_name}", cdr_path
        
        except Exception as e:
            return False, f"Error procesando respuesta: {str(e)}", None
    
    @staticmethod
    def _extraer_cdr(cdr_zip_path: Path, output_dir: Path):
        """Extrae el contenido del CDR (que es un ZIP)"""
        cdr_dir = output_dir / "cdr"
        cdr_dir.mkdir(exist_ok=True)
        
        try:
            with ZipFile(cdr_zip_path, "r") as zip_ref:
                zip_ref.extractall(cdr_dir)
            
            print(f"[OK] CDR extraído en: {cdr_dir}")
            
            # Mostrar XML de respuesta
            for file in cdr_dir.iterdir():
                if file.suffix.lower() == ".xml":
                    print(f"[OK] XML de respuesta: {file}")
                    print("--" * 25)
                    print(file.read_text(encoding="utf-8", errors="ignore"))
                    print("--" * 25)
        
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo extraer el CDR: {e}")


class FileService:
    """Servicio para gestión de archivos"""
    
    @staticmethod
    def guardar_xml(xml_content: str, output_dir: Path, filename: str) -> Path:
        """
        Guarda contenido XML en archivo.
        
        Args:
            xml_content: Contenido XML
            output_dir: Directorio de salida
            filename: Nombre del archivo
            
        Returns:
            Path: Ruta del archivo guardado
        """
        output_dir.mkdir(exist_ok=True)
        file_path = output_dir / filename
        file_path.write_text(xml_content, encoding="utf-8")
        return file_path
    
    @staticmethod
    def generar_nombre_base(ruc: str, tipo_comprobante: str, serie: str, correlativo: int) -> str:
        """Genera nombre base para archivos (RUC-TIPO-SERIE-CORRELATIVO)"""
        return f"{ruc}-{tipo_comprobante}-{serie}-{correlativo}"
