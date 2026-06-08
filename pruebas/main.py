#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
main.py - Interfaz principal para generar, firmar y enviar comprobantes a SUNAT

Uso:
    # Generar boleta sin firma
    python main.py --tipo boleta

    # Generar boleta, firmar y enviar a SUNAT BETA
    python main.py --tipo boleta --sign --send --pfx certificado.pfx --pfx-password "pass"

    # Generar factura
    python main.py --tipo factura --sign --send --pfx certificado.pfx --pfx-password "pass"
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from comprobantes import Boleta, Factura, LineaItem
from firma_envio import FirmaService, ZipService, SunatService, FileService


def crear_boleta_ejemplo():
    """Crea una boleta de ejemplo"""
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",  # DNI
        cliente_num_doc="12345678",
        cliente_nombre="CLIENTE DE PRUEBA",
        serie="B001",
        correlativo=1
    )
    
    # Agregar línea de producto
    linea = LineaItem(
        descripcion="PRODUCTO DE PRUEBA",
        cantidad=1,
        valor_unitario=100.00,
        precio_con_igv=118.00,
        igv_porcentaje=18.00
    )
    boleta.agregar_linea(linea)
    
    return boleta


def crear_factura_ejemplo():
    """Crea una factura de ejemplo"""
    factura = Factura(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="6",  # RUC
        cliente_num_doc="20456789012",
        cliente_nombre="CLIENTE RUC DE PRUEBA",
        serie="F001",
        correlativo=1
    )
    
    # Agregar línea de producto
    linea = LineaItem(
        descripcion="PRODUCTO DE PRUEBA",
        cantidad=2,
        valor_unitario=150.00,
        precio_con_igv=177.00,
        igv_porcentaje=18.00
    )
    factura.agregar_linea(linea)
    
    return factura


def main():
    parser = argparse.ArgumentParser(
        description="Generador, firmador y enviador de comprobantes SUNAT"
    )
    
    parser.add_argument(
        "--tipo",
        choices=["boleta", "factura"],
        default="boleta",
        help="Tipo de comprobante: boleta o factura (default: boleta)"
    )
    
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Firmar el XML con certificado PFX/P12"
    )
    
    parser.add_argument(
        "--send",
        action="store_true",
        help="Enviar el comprobante a SUNAT"
    )
    
    parser.add_argument(
        "--pfx",
        type=str,
        default="certificado.pfx",
        help="Ruta del certificado PFX/P12 (default: certificado.pfx)"
    )
    
    parser.add_argument(
        "--pfx-password",
        type=str,
        default="",
        help="Contraseña del certificado PFX/P12"
    )
    
    parser.add_argument(
        "--ambiente",
        choices=["beta", "produccion"],
        default="beta",
        help="Ambiente SUNAT: beta o produccion (default: beta)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="sunat_output",
        help="Directorio de salida (default: sunat_output)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Crear comprobante
        print(f"[INFO] Creando {args.tipo}...")
        if args.tipo == "boleta":
            comprobante = crear_boleta_ejemplo()
        else:
            comprobante = crear_factura_ejemplo()
        
        # 2. Generar XML
        print("[INFO] Generando XML...")
        xml_content = comprobante.generar_xml()
        
        # 3. Guardar XML
        nombre_base = FileService.generar_nombre_base(
            comprobante.ruc,
            comprobante._get_tipo_codigo_ubl(),
            comprobante.serie,
            comprobante.correlativo
        )
        xml_name = f"{nombre_base}.xml"
        xml_path = FileService.guardar_xml(xml_content, output_dir, xml_name)
        print(f"[OK] XML guardado: {xml_path}")
        
        # 4. Firmar (opcional)
        if args.sign:
            if not args.pfx_password:
                raise RuntimeError("Debes enviar --pfx-password para firmar")
            
            print("[INFO] Firmando XML...")
            pfx_path = Path(args.pfx)
            FirmaService.firmar_xml(xml_path, pfx_path, args.pfx_password)
            print(f"[OK] XML firmado: {xml_path}")
        else:
            print("[ADVERTENCIA] XML generado sin firma")
        
        # 5. Crear ZIP
        print("[INFO] Creando ZIP...")
        zip_path = ZipService.crear_zip(xml_path, output_dir, nombre_base)
        print(f"[OK] ZIP generado: {zip_path}")
        
        # 6. Enviar a SUNAT (opcional)
        if args.send:
            if not args.sign:
                print("[ADVERTENCIA] Enviando sin firma (no recomendado)")
            
            print("[INFO] Conectando con SUNAT...")
            sunat = SunatService(
                usuario_sol=f"{comprobante.ruc}MODDATOS",
                clave_sol="moddatos",
                ambiente=args.ambiente
            )
            
            exito, mensaje, ruta_cdr = sunat.enviar_comprobante(
                zip_path,
                zip_path.name,
                output_dir
            )
            
            if exito:
                print(f"[OK] {mensaje}")
            else:
                print(f"[ERROR] {mensaje}")
                if ruta_cdr:
                    print(f"      {ruta_cdr}")
        else:
            print("[INFO] Comprobante listo. Para enviar a SUNAT usa --send")
        
        # 7. Resumen
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Tipo:              {args.tipo.upper()}")
        print(f"RUC:               {comprobante.ruc}")
        print(f"Serie:             {comprobante.serie}")
        print(f"Correlativo:       {comprobante.correlativo}")
        print(f"Nombre base:       {nombre_base}")
        print(f"XML:               {xml_name}")
        print(f"ZIP:               {zip_path.name}")
        if args.sign:
            print(f"Estado:            FIRMADO")
        else:
            print(f"Estado:            SIN FIRMA")
        if args.send:
            print(f"Enviado a:         SUNAT {args.ambiente.upper()}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
