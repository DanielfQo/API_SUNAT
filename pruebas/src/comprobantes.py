"""
Módulo para generación de comprobantes electrónicos (Boletas y Facturas)
Compatible con UBL 2.1 para SUNAT
"""

from datetime import date
from typing import Optional, List, Dict, Any


class LineaItem:
    """Representa una línea de item en el comprobante"""
    
    def __init__(
        self,
        descripcion: str,
        cantidad: float,
        valor_unitario: float,
        precio_con_igv: float,
        igv_porcentaje: float = 18.00
    ):
        self.descripcion = descripcion
        self.cantidad = float(cantidad)
        self.valor_unitario = float(valor_unitario)
        self.precio_con_igv = float(precio_con_igv)
        self.igv_porcentaje = float(igv_porcentaje)
    
    def calcular_igv(self) -> float:
        """Calcula el IGV para esta línea"""
        base_gravada = self.valor_unitario * self.cantidad
        return base_gravada * (self.igv_porcentaje / 100)
    
    def calcular_subtotal(self) -> float:
        """Calcula el subtotal sin IGV"""
        return self.valor_unitario * self.cantidad
    
    def calcular_total(self) -> float:
        """Calcula el total con IGV"""
        return self.precio_con_igv * self.cantidad


class Comprobante:
    """Clase base para comprobantes (Boleta y Factura)"""
    
    def __init__(
        self,
        ruc: str,
        razon_social: str,
        nombre_comercial: str,
        cliente_tipo_doc: str,
        cliente_num_doc: str,
        cliente_nombre: str,
        serie: str,
        correlativo: int,
        moneda: str = "PEN"
    ):
        self.ruc = ruc
        self.razon_social = razon_social
        self.nombre_comercial = nombre_comercial
        self.cliente_tipo_doc = cliente_tipo_doc
        self.cliente_num_doc = cliente_num_doc
        self.cliente_nombre = cliente_nombre
        self.serie = serie
        self.correlativo = correlativo
        self.moneda = moneda
        self.lineas: List[LineaItem] = []
    
    def agregar_linea(self, linea: LineaItem):
        """Agrega una línea de item al comprobante"""
        self.lineas.append(linea)
    
    def calcular_totales(self) -> Dict[str, float]:
        """Calcula los totales del comprobante"""
        subtotal = sum(l.calcular_subtotal() for l in self.lineas)
        igv_total = sum(l.calcular_igv() for l in self.lineas)
        total = subtotal + igv_total
        
        return {
            "op_gravada": subtotal,
            "igv_total": igv_total,
            "total": total
        }
    
    def _format_money(self, value: float) -> str:
        """Formatea un valor monetario a 2 decimales"""
        return f"{value:.2f}"
    
    def _get_tipo_codigo_ubl(self) -> str:
        """Retorna el código de tipo de comprobante UBL - debe implementarse en subclases"""
        raise NotImplementedError
    
    def _get_customization_id(self) -> str:
        """Retorna el CustomizationID UBL - debe implementarse en subclases"""
        raise NotImplementedError
    
    def generar_xml(self) -> str:
        """Genera el XML UBL 2.1 - método principal"""
        raise NotImplementedError


class Boleta(Comprobante):
    """Representa una Boleta Electrónica"""
    
    def _get_tipo_codigo_ubl(self) -> str:
        """Código UBL para boleta: 03"""
        return "03"
    
    def _get_customization_id(self) -> str:
        """CustomizationID para boleta: 2.0"""
        return "2.0"
    
    def generar_xml(self) -> str:
        """
        Genera un XML UBL 2.1 para boleta electrónica.
        """
        if not self.lineas:
            raise ValueError("La boleta debe tener al menos una línea de item")
        
        totales = self.calcular_totales()
        op_gravada = totales["op_gravada"]
        igv_total = totales["igv_total"]
        total = totales["total"]
        
        # Calcular porcentaje de IGV (asumiendo todas las líneas tienen el mismo IGV)
        igv_porcentaje = self.lineas[0].igv_porcentaje if self.lineas else 18.00
        
        # Generar nota con cantidad en letras (simplificado)
        nota = f"SON {self._convertir_a_letras(total)} {self.moneda}"
        
        # Generar líneas XML
        lineas_xml = self._generar_lineas_xml()
        
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
    <cbc:CustomizationID>{self._get_customization_id()}</cbc:CustomizationID>

    <cbc:ID>{self.serie}-{self.correlativo}</cbc:ID>
    <cbc:IssueDate>{date.today()}</cbc:IssueDate>
    <cbc:IssueTime>00:00:00</cbc:IssueTime>

    <cbc:InvoiceTypeCode listID="0101">{self._get_tipo_codigo_ubl()}</cbc:InvoiceTypeCode>

    <cbc:Note languageLocaleID="1000"><![CDATA[{nota}]]></cbc:Note>

    <cbc:DocumentCurrencyCode>{self.moneda}</cbc:DocumentCurrencyCode>

    <cac:Signature>
        <cbc:ID>{self.ruc}</cbc:ID>
        <cac:SignatoryParty>
            <cac:PartyIdentification>
                <cbc:ID>{self.ruc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{self.razon_social}]]></cbc:Name>
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
                <cbc:ID schemeID="6">{self.ruc}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyName>
                <cbc:Name><![CDATA[{self.nombre_comercial}]]></cbc:Name>
            </cac:PartyName>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{self.razon_social}]]></cbc:RegistrationName>
                <cac:RegistrationAddress>
                    <cbc:AddressTypeCode>0000</cbc:AddressTypeCode>
                </cac:RegistrationAddress>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="{self.cliente_tipo_doc}">{self.cliente_num_doc}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{self.cliente_nombre}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>

    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv_total)}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="{self.moneda}">{self._format_money(op_gravada)}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv_total)}</cbc:TaxAmount>
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
        <cbc:LineExtensionAmount currencyID="{self.moneda}">{self._format_money(op_gravada)}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="{self.moneda}">{self._format_money(total)}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{self.moneda}">{self._format_money(total)}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>

{lineas_xml}
</Invoice>
'''
        return xml_content
    
    def _generar_lineas_xml(self) -> str:
        """Genera el XML para cada línea de item"""
        lineas_xml = ""
        for idx, linea in enumerate(self.lineas, 1):
            subtotal = linea.calcular_subtotal()
            igv = linea.calcular_igv()
            
            lineas_xml += f'''    <cac:InvoiceLine>
        <cbc:ID>{idx}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">{linea.cantidad}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{self.moneda}">{self._format_money(subtotal)}</cbc:LineExtensionAmount>

        <cac:PricingReference>
            <cac:AlternativeConditionPrice>
                <cbc:PriceAmount currencyID="{self.moneda}">{self._format_money(linea.precio_con_igv)}</cbc:PriceAmount>
                <cbc:PriceTypeCode>01</cbc:PriceTypeCode>
            </cac:AlternativeConditionPrice>
        </cac:PricingReference>

        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv)}</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="{self.moneda}">{self._format_money(subtotal)}</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv)}</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:Percent>{self._format_money(linea.igv_porcentaje)}</cbc:Percent>
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
            <cbc:Description><![CDATA[{linea.descripcion}]]></cbc:Description>
        </cac:Item>

        <cac:Price>
            <cbc:PriceAmount currencyID="{self.moneda}">{self._format_money(linea.valor_unitario)}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
'''
        return lineas_xml
    
    def _convertir_a_letras(self, cantidad: float) -> str:
        """
        Convierte un número a letras (versión simplificada).
        En producción, usar una librería como num2words
        """
        # Versión simplificada - devuelve cantidad formateada
        return f"{cantidad:.2f}".replace(".", " CON ")


class Factura(Comprobante):
    """Representa una Factura Electrónica"""
    
    def __init__(
        self,
        ruc: str,
        razon_social: str,
        nombre_comercial: str,
        cliente_tipo_doc: str,
        cliente_num_doc: str,
        cliente_nombre: str,
        serie: str,
        correlativo: int,
        moneda: str = "PEN"
    ):
        super().__init__(
            ruc, razon_social, nombre_comercial,
            cliente_tipo_doc, cliente_num_doc, cliente_nombre,
            serie, correlativo, moneda
        )
        # Cliente debe ser RUC para facturas
        if cliente_tipo_doc != "6":
            raise ValueError("Para Factura, el cliente debe ser RUC (schemeID='6')")
    
    def _get_tipo_codigo_ubl(self) -> str:
        """Código UBL para factura: 01"""
        return "01"
    
    def _get_customization_id(self) -> str:
        """CustomizationID para factura: 2.1"""
        return "2.1"
    

    def _get_transaction_type_code(self) -> str:
        """TransactionTypeCode para factura: 0101 (Operación Gravada - Venta)"""
        return "0101"
    
    def generar_xml(self) -> str:
        """
        Genera un XML UBL 2.1 para factura electrónica.
        Similar a boleta, con ajustes específicos de factura.
        """
        if not self.lineas:
            raise ValueError("La factura debe tener al menos una línea de item")
        
        totales = self.calcular_totales()
        op_gravada = totales["op_gravada"]
        igv_total = totales["igv_total"]
        total = totales["total"]
        
        # Calcular porcentaje de IGV
        igv_porcentaje = self.lineas[0].igv_porcentaje if self.lineas else 18.00
        
        # Nota con cantidad en letras
        nota = f"SON {self._convertir_a_letras(total)} {self.moneda}"
        
        # Generar líneas XML
        lineas_xml = self._generar_lineas_xml()
        
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
    <cbc:CustomizationID>{self._get_customization_id()}</cbc:CustomizationID>

    <cbc:ID>{self.serie}-{self.correlativo}</cbc:ID>
    <cbc:IssueDate>{date.today()}</cbc:IssueDate>
    <cbc:IssueTime>00:00:00</cbc:IssueTime>

    <cbc:InvoiceTypeCode listID="0101">{self._get_tipo_codigo_ubl()}</cbc:InvoiceTypeCode>

    <cbc:Note languageLocaleID="1000"><![CDATA[{nota}]]></cbc:Note>

    <cbc:DocumentCurrencyCode>{self.moneda}</cbc:DocumentCurrencyCode>

    <cac:Signature>
        <cbc:ID>{self.ruc}</cbc:ID>
        <cac:SignatoryParty>
            <cac:PartyIdentification>
                <cbc:ID>{self.ruc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{self.razon_social}]]></cbc:Name>
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
                <cbc:ID schemeID="6">{self.ruc}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyName>
                <cbc:Name><![CDATA[{self.nombre_comercial}]]></cbc:Name>
            </cac:PartyName>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{self.razon_social}]]></cbc:RegistrationName>
                <cac:RegistrationAddress>
                    <cbc:AddressTypeCode>0000</cbc:AddressTypeCode>
                </cac:RegistrationAddress>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="{self.cliente_tipo_doc}">{self.cliente_num_doc}</cbc:ID>
            </cac:PartyIdentification>

            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{self.cliente_nombre}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>

    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv_total)}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="{self.moneda}">{self._format_money(op_gravada)}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv_total)}</cbc:TaxAmount>
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
        <cbc:LineExtensionAmount currencyID="{self.moneda}">{self._format_money(op_gravada)}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="{self.moneda}">{self._format_money(total)}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{self.moneda}">{self._format_money(total)}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>

{lineas_xml}
</Invoice>
'''
        return xml_content
    
    def _generar_lineas_xml(self) -> str:
        """Genera el XML para cada línea de item"""
        lineas_xml = ""
        for idx, linea in enumerate(self.lineas, 1):
            subtotal = linea.calcular_subtotal()
            igv = linea.calcular_igv()
            
            lineas_xml += f'''    <cac:InvoiceLine>
        <cbc:ID>{idx}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">{linea.cantidad}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{self.moneda}">{self._format_money(subtotal)}</cbc:LineExtensionAmount>

        <cac:PricingReference>
            <cac:AlternativeConditionPrice>
                <cbc:PriceAmount currencyID="{self.moneda}">{self._format_money(linea.precio_con_igv)}</cbc:PriceAmount>
                <cbc:PriceTypeCode>01</cbc:PriceTypeCode>
            </cac:AlternativeConditionPrice>
        </cac:PricingReference>

        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv)}</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cbc:TaxableAmount currencyID="{self.moneda}">{self._format_money(subtotal)}</cbc:TaxableAmount>
                <cbc:TaxAmount currencyID="{self.moneda}">{self._format_money(igv)}</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:Percent>{self._format_money(linea.igv_porcentaje)}</cbc:Percent>
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
            <cbc:Description><![CDATA[{linea.descripcion}]]></cbc:Description>
        </cac:Item>

        <cac:Price>
            <cbc:PriceAmount currencyID="{self.moneda}">{self._format_money(linea.valor_unitario)}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
'''
        return lineas_xml
    
    def _convertir_a_letras(self, cantidad: float) -> str:
        """Convierte un número a letras (versión simplificada)"""
        return f"{cantidad:.2f}".replace(".", " CON ")
