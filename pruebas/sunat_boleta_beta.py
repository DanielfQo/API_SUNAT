#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sunat_boleta_beta.py

Script completo para:
1. Generar XML UBL 2.1 de boleta electrónica.
2. Firmar el XML con certificado .pfx/.p12.
3. Crear ZIP compatible con SUNAT.
4. Enviar el ZIP al servicio BETA de SUNAT usando sendBill.
5. Guardar el CDR de respuesta.

Instalación de dependencias:

    pip install lxml signxml cryptography zeep requests

Uso básico solo para generar XML y ZIP sin firma:

    python sunat_boleta_beta.py

Uso firmando XML:

    python sunat_boleta_beta.py --sign --pfx certificado.pfx --pfx-password "TU_PASSWORD"

Uso firmando y enviando a SUNAT BETA:

    python sunat_boleta_beta.py --sign --send --pfx certificado.pfx --pfx-password "TU_PASSWORD"

IMPORTANTE:
- Para BETA normalmente se usa:
    usuario SOL = RUC + "MODDATOS"
    clave SOL   = "moddatos"
- Para producción debes usar credenciales reales y endpoint productivo.
"""

import argparse
from datetime import date
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree


RUC = "10763375621"
RAZON_SOCIAL = "EMPRESA DE PRUEBA SAC"
NOMBRE_COMERCIAL = "EMPRESA DE PRUEBA"

TIPO_COMPROBANTE = "03"   # 03 = Boleta
SERIE = "B001"
CORRELATIVO = "1"

MONEDA = "PEN"

CLIENTE_TIPO_DOC = "1"    # 1 = DNI, 6 = RUC, 0 = Doc. no domiciliado
CLIENTE_NUM_DOC = "12345678"
CLIENTE_NOMBRE = "CLIENTE DE PRUEBA"

PRODUCTO_DESCRIPCION = "PRODUCTO DE PRUEBA"
PRODUCTO_CANTIDAD = "1"
PRODUCTO_VALOR_UNITARIO = 100.00
PRODUCTO_PRECIO_CON_IGV = 118.00

IGV_PORCENTAJE = 18.00
OP_GRAVADA = 100.00
IGV_TOTAL = 18.00
TOTAL = 118.00

OUTPUT_DIR = Path("sunat_output")

WSDL_BETA = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"



def money(value: float) -> str:
    return f"{value:.2f}"


def get_nombre_base() -> str:
    return f"{RUC}-{TIPO_COMPROBANTE}-{SERIE}-{CORRELATIVO}"


def get_paths():
    OUTPUT_DIR.mkdir(exist_ok=True)

    nombre_base = get_nombre_base()
    xml_name = f"{nombre_base}.xml"
    zip_name = f"{nombre_base}.zip"

    xml_path = OUTPUT_DIR / xml_name
    zip_path = OUTPUT_DIR / zip_name

    return nombre_base, xml_name, zip_name, xml_path, zip_path



def generar_xml_boleta() -> str:
    """
    Genera un XML UBL 2.1 básico para boleta electrónica gravada con IGV.
    """

    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
         xmlns:ds="http://www.w3.org/2000/09/xmldsig#">

    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
            </ext:ExtensionContent>
        </ext:UBLExtension>
    </ext:UBLExtensions>

    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>

    <cbc:ID>{SERIE}-{CORRELATIVO}</cbc:ID>
    <cbc:IssueDate>{date.today()}</cbc:IssueDate>
    <cbc:IssueTime>00:00:00</cbc:IssueTime>

    <cbc:InvoiceTypeCode listID="0101">03</cbc:InvoiceTypeCode>

    <cbc:Note languageLocaleID="1000"><![CDATA[SON CIENTO DIECIOCHO CON 00/100 SOLES]]></cbc:Note>

    <cbc:DocumentCurrencyCode>{MONEDA}</cbc:DocumentCurrencyCode>

    <cac:Signature>
        <cbc:ID>{RUC}</cbc:ID>
        <cac:SignatoryParty>
            <cac:PartyIdentification>
                <cbc:ID>{RUC}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{RAZON_SOCIAL}]]></cbc:Name>
            </cac:PartyName>
        </cac:SignatoryParty>
        <cac:DigitalSignatureAttachment>
            <cac:ExternalReference>
                <cbc:URI>#signatureKG</cbc:URI>
            </cac:ExternalReference>
        </cac:DigitalSignatureAttachment>
    </cac:Signature>

    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">{RUC}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyName>
                <cbc:Name><![CDATA[{NOMBRE_COMERCIAL}]]></cbc:Name>
            </cac:PartyName>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{RAZON_SOCIAL}]]></cbc:RegistrationName>
                <cac:RegistrationAddress>
                    <cbc:AddressTypeCode>0000</cbc:AddressTypeCode>
                </cac:RegistrationAddress>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="{CLIENTE_TIPO_DOC}">{CLIENTE_NUM_DOC}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{CLIENTE_NOMBRE}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>

    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{MONEDA}">{money(IGV_TOTAL)}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="{MONEDA}">{money(OP_GRAVADA)}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="{MONEDA}">{money(IGV_TOTAL)}</cbc:TaxAmount>
            <cac:TaxCategory>
                <cac:TaxScheme>
                    <cbc:ID>1000</cbc:ID>
                    <cbc:Name>IGV</cbc:Name>
                    <cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>

    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="{MONEDA}">{money(OP_GRAVADA)}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="{MONEDA}">{money(TOTAL)}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{MONEDA}">{money(TOTAL)}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>

    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">{PRODUCTO_CANTIDAD}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{MONEDA}">{money(OP_GRAVADA)}</cbc:LineExtensionAmount>

        <cac:PricingReference>
            <cac:AlternativeConditionPrice>
                <cbc:PriceAmount currencyID="{MONEDA}">{money(PRODUCTO_PRECIO_CON_IGV)}</cbc:PriceAmount>
                <cbc:PriceTypeCode>01</cbc:PriceTypeCode>
            </cac:AlternativeConditionPrice>
        </cac:PricingReference>

        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="{MONEDA}">{money(IGV_TOTAL)}</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="{MONEDA}">{money(OP_GRAVADA)}</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="{MONEDA}">{money(IGV_TOTAL)}</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:Percent>{money(IGV_PORCENTAJE)}</cbc:Percent>
                    <cbc:TaxExemptionReasonCode>10</cbc:TaxExemptionReasonCode>
                    <cac:TaxScheme>
                        <cbc:ID>1000</cbc:ID>
                        <cbc:Name>IGV</cbc:Name>
                        <cbc:TaxTypeCode>VAT</cbc:TaxTypeCode>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>

        <cac:Item>
            <cbc:Description><![CDATA[{PRODUCTO_DESCRIPCION}]]></cbc:Description>
        </cac:Item>

        <cac:Price>
            <cbc:PriceAmount currencyID="{MONEDA}">{money(PRODUCTO_VALOR_UNITARIO)}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>
'''
    return xml_content


def guardar_xml(xml_content: str, xml_path: Path):
    xml_path.write_text(xml_content, encoding="utf-8")




def firmar_xml_con_pfx(xml_path: Path, pfx_path: Path, pfx_password: str):
    """
    Firma el XML usando un certificado .pfx/.p12.

    La firma generada se mueve dentro de:
        ext:UBLExtensions / ext:UBLExtension / ext:ExtensionContent
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

    if not pfx_path.exists():
        raise FileNotFoundError(f"No existe el certificado: {pfx_path}")

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, _ = load_key_and_certificates(
        pfx_data,
        pfx_password.encode("utf-8")
    )

    if private_key is None or certificate is None:
        raise RuntimeError("No se pudo leer la llave privada o el certificado desde el PFX/P12.")

    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    cert_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM
    )

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(xml_path), parser).getroot()

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
        raise RuntimeError("No se generó la firma XMLDSig.")

    if extension_content is None:
        raise RuntimeError("No se encontró ext:ExtensionContent para insertar la firma.")

    parent = signature.getparent()
    if parent is not None:
        parent.remove(signature)

    extension_content.append(signature)

    tree = etree.ElementTree(signed_root)
    tree.write(
        str(xml_path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False
    )


# ============================================================
# ZIP
# ============================================================

def crear_zip(xml_path: Path, zip_path: Path, xml_name: str):
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
        zip_file.write(xml_path, arcname=xml_name)


# ============================================================
# ENVÍO SUNAT BETA
# ============================================================

def enviar_sunat_beta(zip_path: Path, zip_name: str):
    """
    Envía el ZIP a SUNAT BETA usando SOAP manual con requests.
    Evita el error 401 de zeep al descargar XSD importados del WSDL.
    """

    import base64
    import requests
    from lxml import etree

    usuario_sol = RUC + "MODDATOS"
    clave_sol = "MODDATOS"

    url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"

    zip_base64 = base64.b64encode(zip_path.read_bytes()).decode("utf-8")

    soap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:ser="http://service.sunat.gob.pe"
                  xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soapenv:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>{usuario_sol}</wsse:Username>
                <wsse:Password>{clave_sol}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <ser:sendBill>
            <fileName>{zip_name}</fileName>
            <contentFile>{zip_base64}</contentFile>
        </ser:sendBill>
    </soapenv:Body>
</soapenv:Envelope>'''

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "urn:sendBill",
    }

    print("[INFO] Enviando SOAP manual a SUNAT BETA...")

    response = requests.post(
        url,
        data=soap_xml.encode("utf-8"),
        headers=headers,
        timeout=60
    )

    print("[INFO] HTTP Status:", response.status_code)

    if response.status_code != 200:
        print("[ERROR] Respuesta HTTP de SUNAT:")
        print(response.text)
        return

    root = etree.fromstring(response.content)

    fault = root.find(".//faultstring")
    if fault is not None:
        print("[ERROR SOAP SUNAT]")
        print(fault.text)
        return

    app_response = root.find(".//applicationResponse")

    if app_response is None:
        print("[ADVERTENCIA] SUNAT respondió, pero no se encontró applicationResponse.")
        print(response.text)
        return

    cdr_base64 = app_response.text
    cdr_bytes = base64.b64decode(cdr_base64)

    cdr_name = f"R-{zip_name}"
    cdr_path = OUTPUT_DIR / cdr_name
    cdr_path.write_bytes(cdr_bytes)

    print(f"[OK] CDR guardado: {cdr_path}")

    extraer_cdr(cdr_path)

def extraer_cdr(cdr_zip_path: Path):
    cdr_dir = OUTPUT_DIR / "cdr"
    cdr_dir.mkdir(exist_ok=True)

    try:
        with ZipFile(cdr_zip_path, "r") as zip_ref:
            zip_ref.extractall(cdr_dir)

        print(f"[OK] CDR extraído en: {cdr_dir}")

        for file in cdr_dir.iterdir():
            if file.suffix.lower() == ".xml":
                print(f"[OK] XML de respuesta: {file}")
                print("--------------------------------------------------")
                print(file.read_text(encoding="utf-8", errors="ignore"))
                print("--------------------------------------------------")

    except Exception as e:
        print("[ADVERTENCIA] No se pudo extraer el CDR.")
        print(e)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generar, firmar y enviar boleta electrónica a SUNAT BETA."
    )

    parser.add_argument(
        "--sign",
        action="store_true",
        help="Firma el XML con certificado PFX/P12."
    )

    parser.add_argument(
        "--send",
        action="store_true",
        help="Envía el ZIP firmado a SUNAT BETA."
    )

    parser.add_argument(
        "--pfx",
        type=str,
        default="certificado.pfx",
        help="Ruta del certificado .pfx/.p12."
    )

    parser.add_argument(
        "--pfx-password",
        type=str,
        default="",
        help="Contraseña del certificado .pfx/.p12."
    )

    args = parser.parse_args()

    nombre_base, xml_name, zip_name, xml_path, zip_path = get_paths()

    print("[INFO] Generando XML...")
    xml_content = generar_xml_boleta()
    guardar_xml(xml_content, xml_path)
    print(f"[OK] XML generado: {xml_path}")

    if args.sign:
        if not args.pfx_password:
            raise RuntimeError("Debes enviar la contraseña del certificado con --pfx-password.")

        print("[INFO] Firmando XML...")
        firmar_xml_con_pfx(
            xml_path=xml_path,
            pfx_path=Path(args.pfx),
            pfx_password=args.pfx_password
        )
        print(f"[OK] XML firmado: {xml_path}")
    else:
        print("[ADVERTENCIA] XML generado sin firma.")

    print("[INFO] Creando ZIP...")
    crear_zip(xml_path, zip_path, xml_name)
    print(f"[OK] ZIP generado: {zip_path}")

    print("--------------------------------------------------")
    print(f"Nombre base: {nombre_base}")
    print(f"XML: {xml_name}")
    print(f"ZIP: {zip_name}")
    print("--------------------------------------------------")

    if args.send:
        if not args.sign:
            print("[ADVERTENCIA] Estás intentando enviar sin firmar")
        print("[INFO] Enviando a SUNAT BETA...")
        enviar_sunat_beta(zip_path, zip_name)
    else:
        print("[INFO] No se envioa SUNAT. Para enviar usa --send.")


if __name__ == "__main__":
    main()
