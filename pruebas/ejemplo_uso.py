#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ejemplo_uso.py - Ejemplos de uso programático de los módulos

Este archivo muestra diferentes formas de usar la librería:
- Crear y generar XML de boleta
- Crear y generar XML de factura
- Firmar XML
- Enviar a SUNAT
- Procesar CDR
"""

import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from comprobantes import Boleta, Factura, LineaItem
from firma_envio import FirmaService, ZipService, SunatService, FileService

PFX_PATH = Path(os.getenv("SUNAT_PFX_PATH", "certificado_prueba.pfx"))
PFX_PASSWORD = os.getenv("SUNAT_PFX_PASSWORD", "123456")


def ejemplo_1_generar_boleta_basica():
    """Ejemplo 1: Generar una boleta básica sin firma"""
    print("\n" + "="*60)
    print("EJEMPLO 1: Generar Boleta Básica")
    print("="*60)
    
    # Crear boleta
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",      # DNI
        cliente_num_doc="12345678",
        cliente_nombre="JUAN PEREZ",
        serie="B001",
        correlativo=1
    )
    
    # Agregar productos
    linea1 = LineaItem(
        descripcion="LAPTOP",
        cantidad=1,
        valor_unitario=3000.00,
        precio_con_igv=3540.00
    )
    
    linea2 = LineaItem(
        descripcion="MOUSE",
        cantidad=2,
        valor_unitario=50.00,
        precio_con_igv=59.00
    )
    
    boleta.agregar_linea(linea1)
    boleta.agregar_linea(linea2)
    
    # Generar XML
    xml_content = boleta.generar_xml()
    
    # Guardar
    output_dir = Path("sunat_output")
    xml_path = FileService.guardar_xml(
        xml_content,
        output_dir,
        "boleta_ejemplo1.xml"
    )
    
    print(f"✓ XML generado: {xml_path}")
    
    # Mostrar totales
    totales = boleta.calcular_totales()
    print(f"  Op. Gravada:  S/ {totales['op_gravada']:.2f}")
    print(f"  IGV (18%):    S/ {totales['igv_total']:.2f}")
    print(f"  TOTAL:        S/ {totales['total']:.2f}")


def ejemplo_2_generar_factura():
    """Ejemplo 2: Generar una factura (requiere cliente RUC)"""
    print("\n" + "="*60)
    print("EJEMPLO 2: Generar Factura")
    print("="*60)
    
    try:
        # Crear factura
        factura = Factura(
            ruc="10763375621",
            razon_social="EMPRESA DE PRUEBA SAC",
            nombre_comercial="EMPRESA DE PRUEBA",
            cliente_tipo_doc="6",      # RUC (REQUERIDO para factura)
            cliente_num_doc="20456789012",
            cliente_nombre="EMPRESA CLIENTE SAC",
            serie="F001",
            correlativo=1
        )
        
        # Agregar servicio
        linea = LineaItem(
            descripcion="CONSULTORÍA DE TI",
            cantidad=10,
            valor_unitario=500.00,
            precio_con_igv=590.00
        )
        factura.agregar_linea(linea)
        
        # Generar XML
        xml_content = factura.generar_xml()
        
        # Guardar
        output_dir = Path("sunat_output")
        xml_path = FileService.guardar_xml(
            xml_content,
            output_dir,
            "factura_ejemplo2.xml"
        )
        
        print(f"✓ XML generado: {xml_path}")
        
        # Mostrar totales
        totales = factura.calcular_totales()
        print(f"  Op. Gravada:  S/ {totales['op_gravada']:.2f}")
        print(f"  IGV (18%):    S/ {totales['igv_total']:.2f}")
        print(f"  TOTAL:        S/ {totales['total']:.2f}")
    
    except ValueError as e:
        print(f"✗ Error: {e}")


def ejemplo_3_crear_y_comprimir():
    """Ejemplo 3: Generar XML y crear ZIP"""
    print("\n" + "="*60)
    print("EJEMPLO 3: Generar XML y Crear ZIP")
    print("="*60)
    
    # Crear boleta
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",
        cliente_num_doc="98765432",
        cliente_nombre="MARIA LOPEZ",
        serie="B002",
        correlativo=5
    )
    
    linea = LineaItem(
        descripcion="SERVICIO DE MANTENIMIENTO",
        cantidad=1,
        valor_unitario=200.00,
        precio_con_igv=236.00
    )
    boleta.agregar_linea(linea)
    
    # Generar XML
    xml_content = boleta.generar_xml()

    # Guardar XML usando el nombre_base requerido por SUNAT
    output_dir = Path("sunat_output")
    nombre_base = FileService.generar_nombre_base(
        boleta.ruc,
        boleta._get_tipo_codigo_ubl(),
        boleta.serie,
        boleta.correlativo
    )

    xml_path = FileService.guardar_xml(
        xml_content,
        output_dir,
        f"{nombre_base}.xml"
    )
    print(f"✓ XML guardado: {xml_path}")

    # Crear ZIP con el mismo nombre_base
    zip_path = ZipService.crear_zip(xml_path, output_dir, nombre_base)
    print(f"✓ ZIP creado: {zip_path}")


def ejemplo_4_firmar_xml():
    """Ejemplo 4: Firmar un XML (requiere certificado PFX)"""
    print("\n" + "="*60)
    print("EJEMPLO 4: Firmar XML")
    print("="*60)
    
    # Nota: Este ejemplo requiere un certificado válido
    
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",
        cliente_num_doc="11111111",
        cliente_nombre="CLIENTE FIRMADO",
        serie="B003",
        correlativo=10
    )
    
    linea = LineaItem(
        descripcion="PRODUCTO FIRMADO",
        cantidad=1,
        valor_unitario=500.00,
        precio_con_igv=590.00
    )
    boleta.agregar_linea(linea)
    
    # Generar y guardar XML usando nombre_base (para consistencia si luego zipeas/envías)
    xml_content = boleta.generar_xml()
    output_dir = Path("sunat_output")
    nombre_base = FileService.generar_nombre_base(
        boleta.ruc,
        boleta._get_tipo_codigo_ubl(),
        boleta.serie,
        boleta.correlativo
    )
    xml_path = FileService.guardar_xml(
        xml_content,
        output_dir,
        f"{nombre_base}.xml"
    )
    print(f"✓ XML generado: {xml_path}")
    
    # Intentar firmar
    pfx_path = PFX_PATH
    if pfx_path.exists():
        try:
            FirmaService.firmar_xml(
                xml_path=xml_path,
                pfx_path=pfx_path,
                pfx_password=PFX_PASSWORD
            )
            print(f"✓ XML firmado correctamente")
        except Exception as e:
            print(f"✗ Error al firmar: {e}")
            print(f"  Verifica que el certificado y contraseña sean correctos")
    else:
        print(f"⚠ Certificado no encontrado: {pfx_path}")
        print(f"  Coloca tu certificado en: {pfx_path}")


def ejemplo_5_enviar_sunat():
    """Ejemplo 5: Enviar comprobante a SUNAT BETA"""
    print("\n" + "="*60)
    print("EJEMPLO 5: Enviar a SUNAT BETA")
    print("="*60)
    
    print("\n⚠ Para este ejemplo necesitas:")
    print("  1. Un certificado firmado válido")
    print("  2. Credenciales de SUNAT BETA válidas")
    print("  3. Conexión a Internet")
    
    # Crear boleta
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",
        cliente_num_doc="22222222",
        cliente_nombre="CLIENTE PARA ENVIAR",
        serie="B004",
        correlativo=15
    )
    
    linea = LineaItem(
        descripcion="PRODUCTO PARA SUNAT",
        cantidad=1,
        valor_unitario=100.00,
        precio_con_igv=118.00
    )
    boleta.agregar_linea(linea)
    
    # Generar XML y guardarlo con el nombre_base requerido por SUNAT
    xml_content = boleta.generar_xml()
    output_dir = Path("sunat_output")
    nombre_base = FileService.generar_nombre_base(
        boleta.ruc,
        boleta._get_tipo_codigo_ubl(),
        boleta.serie,
        boleta.correlativo
    )
    xml_path = FileService.guardar_xml(
        xml_content,
        output_dir,
        f"{nombre_base}.xml"
    )
    print(f"✓ XML generado: {xml_path}")
    
    # Firmar
    pfx_path = PFX_PATH
    if not pfx_path.exists():
        print(f"✗ Certificado no encontrado: {pfx_path}")
        return
    
    try:
        FirmaService.firmar_xml(
            xml_path=xml_path,
            pfx_path=pfx_path,
            pfx_password=PFX_PASSWORD
        )
        print(f"✓ XML firmado")
    except Exception as e:
        print(f"✗ Error al firmar: {e}")
        return
    
    # Crear ZIP
    nombre_base = FileService.generar_nombre_base(
        boleta.ruc,
        boleta._get_tipo_codigo_ubl(),
        boleta.serie,
        boleta.correlativo
    )
    zip_path = ZipService.crear_zip(xml_path, output_dir, nombre_base)
    print(f"✓ ZIP creado: {zip_path}")
    
    # Enviar a SUNAT
    print(f"\n[INFO] Enviando a SUNAT BETA...")
    sunat = SunatService(
        usuario_sol="10763375621MODDATOS",
        clave_sol="moddatos",
        ambiente="beta"
    )
    
    exito, mensaje, cdr_path = sunat.enviar_comprobante(
        zip_path=zip_path,
        zip_nombre=zip_path.name,
        output_dir=output_dir
    )
    
    if exito:
        print(f"✓ {mensaje}")
        if cdr_path:
            print(f"  CDR guardado en: {cdr_path}")
    else:
        print(f"✗ {mensaje}")


def ejemplo_6_multiples_lineas():
    """Ejemplo 6: Boleta con múltiples líneas y cálculos"""
    print("\n" + "="*60)
    print("EJEMPLO 6: Boleta con Múltiples Líneas")
    print("="*60)
    
    boleta = Boleta(
        ruc="10763375621",
        razon_social="EMPRESA DE PRUEBA SAC",
        nombre_comercial="EMPRESA DE PRUEBA",
        cliente_tipo_doc="1",
        cliente_num_doc="33333333",
        cliente_nombre="CLIENTE MULTIPLE",
        serie="B005",
        correlativo=20
    )
    
    # Agregar múltiples productos
    productos = [
        ("ARROZ 1KG", 5, 10.00, 11.80),
        ("AZÚCAR 1KG", 3, 8.00, 9.44),
        ("ACEITE 1L", 2, 6.00, 7.08),
        ("PAN FRANCÉS", 10, 1.50, 1.77),
    ]
    
    for desc, cant, valor, precio_igv in productos:
        linea = LineaItem(
            descripcion=desc,
            cantidad=cant,
            valor_unitario=valor,
            precio_con_igv=precio_igv
        )
        boleta.agregar_linea(linea)
    
    # Calcular y mostrar totales
    totales = boleta.calcular_totales()
    print(f"\n Detalles:")
    for i, linea in enumerate(boleta.lineas, 1):
        print(f"  Línea {i}: {linea.descripcion}")
        print(f"    Cantidad: {linea.cantidad} x S/ {linea.valor_unitario:.2f}")
        print(f"    Subtotal: S/ {linea.calcular_subtotal():.2f}")
        print(f"    IGV: S/ {linea.calcular_igv():.2f}")
        print(f"    Total: S/ {linea.calcular_total():.2f}")
    
    print(f"\n Totales:")
    print(f"  Op. Gravada: S/ {totales['op_gravada']:.2f}")
    print(f"  IGV (18%):   S/ {totales['igv_total']:.2f}")
    print(f"  TOTAL:       S/ {totales['total']:.2f}")
    
    # Generar XML
    xml_content = boleta.generar_xml()
    output_dir = Path("sunat_output")
    xml_path = FileService.guardar_xml(
        xml_content,
        output_dir,
        "boleta_ejemplo6.xml"
    )
    print(f"\n✓ XML generado: {xml_path}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EJEMPLOS DE USO - Sistema SUNAT Modularizado")
    print("="*60)
    
    # Ejecutar ejemplos
    ejemplo_1_generar_boleta_basica()
    ejemplo_2_generar_factura()
    ejemplo_3_crear_y_comprimir()
    ejemplo_4_firmar_xml()
    ejemplo_5_enviar_sunat()
    ejemplo_6_multiples_lineas()
    
    print("\n" + "="*60)
    print("✓ Ejemplos completados")
    print("="*60)
    print("\nRevisa los archivos generados en: sunat_output/")
