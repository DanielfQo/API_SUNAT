# 🏗️ Arquitectura de Módulos - Diagramas

## 📊 Diagrama de Dependencias

```mermaid
graph TD
    main["main.py<br/>(CLI)"]
    
    comprobantes["src/comprobantes.py<br/>(Generación XML)"]
    firma_envio["src/firma_envio.py<br/>(Firma & Envío)"]
    
    ejemplo["ejemplo_uso.py<br/>(Ejemplos)"]
    
    subgraph Clases de Comprobante
        LineaItem["LineaItem<br/>- cantidad<br/>- valor_unitario<br/>- calcular_igv()"]
        Comprobante["Comprobante<br/>- lineas[]<br/>- calcular_totales()"]
        Boleta["Boleta<br/>- serie<br/>- correlativo<br/>- generar_xml()"]
        Factura["Factura<br/>- validar RUC<br/>- generar_xml()"]
    end
    
    subgraph Servicios
        FileService["FileService<br/>- guardar_xml()<br/>- generar_nombre_base()"]
        FirmaService["FirmaService<br/>- firmar_xml()"]
        ZipService["ZipService<br/>- crear_zip()"]
        SunatService["SunatService<br/>- enviar_comprobante()"]
    end
    
    main -->|usa| comprobantes
    main -->|usa| firma_envio
    ejemplo -->|usa| comprobantes
    ejemplo -->|usa| firma_envio
    
    comprobantes --> LineaItem
    comprobantes --> Comprobante
    Comprobante --> Boleta
    Comprobante --> Factura
    
    firma_envio --> FileService
    firma_envio --> FirmaService
    firma_envio --> ZipService
    firma_envio --> SunatService
    
    Boleta -->|usa| FileService
    Factura -->|usa| FileService
```

---

## 🔄 Flujo de Procesamiento

```mermaid
flowchart TD
    A["1. Crear Comprobante<br/>Boleta o Factura"]
    B["2. Agregar LineaItems<br/>Productos/Servicios"]
    C["3. Generar XML<br/>UBL 2.1"]
    D["4. Guardar XML<br/>FileService"]
    E{¿Firmar?}
    F["5. Firmar XML<br/>FirmaService"]
    G["6. Crear ZIP<br/>ZipService"]
    H{¿Enviar a SUNAT?}
    I["7. Enviar a SUNAT<br/>SunatService"]
    J["8. Procesar CDR<br/>Respuesta"]
    K["✓ Completado"]
    L["⚠ Sin firma"]
    M["ℹ ZIP Listo"]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E -->|Sí| F
    E -->|No| L
    F --> G
    L --> G
    G --> H
    H -->|Sí| I
    H -->|No| M
    I --> J
    J --> K
    M --> K
```

---

## 📦 Estructura de Clases

```mermaid
classDiagram
    class LineaItem {
        - descripcion: str
        - cantidad: float
        - valor_unitario: float
        - precio_con_igv: float
        - igv_porcentaje: float
        + calcular_subtotal() float
        + calcular_igv() float
        + calcular_total() float
    }
    
    class Comprobante {
        <<abstract>>
        - ruc: str
        - razon_social: str
        - cliente_tipo_doc: str
        - serie: str
        - correlativo: int
        - lineas: List~LineaItem~
        + agregar_linea(LineaItem)
        + calcular_totales() Dict
        + generar_xml() str*
    }
    
    class Boleta {
        - cliente_puede_ser_consumidor: bool
        + generar_xml() str
        + _get_tipo_codigo_ubl() str
        + _get_customization_id() str
    }
    
    class Factura {
        - cliente_debe_ser_ruc: bool
        + generar_xml() str
        + _get_tipo_codigo_ubl() str
        + _get_customization_id() str
    }
    
    class FirmaService {
        <<static>>
        + firmar_xml(xml_path, pfx_path, pfx_password) bool
    }
    
    class ZipService {
        <<static>>
        + crear_zip(xml_path, output_dir, nombre_base) Path
    }
    
    class SunatService {
        - usuario_sol: str
        - clave_sol: str
        - ambiente: str
        + enviar_comprobante(zip_path, zip_nombre) Tuple
    }
    
    class FileService {
        <<static>>
        + guardar_xml(xml_content, output_dir, filename) Path
        + generar_nombre_base(ruc, tipo, serie, correlativo) str
    }
    
    Comprobante <|-- Boleta
    Comprobante <|-- Factura
    Comprobante --> LineaItem
```

---

## 🔗 Flujo de Datos

```mermaid
graph LR
    A["Datos de Entrada<br/>RUC, Cliente, Items"]
    B["Boleta/Factura<br/>Objeto"]
    C["XML String<br/>UBL 2.1"]
    D["Archivo .xml<br/>Sin firmar"]
    E["Archivo .xml<br/>FIRMADO"]
    F["Archivo .zip<br/>Comprimido"]
    G["SUNAT<br/>Envío"]
    H["CDR ZIP<br/>Respuesta"]
    I["Archivos CDR<br/>Procesados"]
    
    A -->|Crear| B
    B -->|Generar| C
    C -->|Guardar| D
    D -->|Firmar| E
    E -->|Comprimir| F
    F -->|Enviar| G
    G -->|Respuesta| H
    H -->|Extraer| I
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#fce4ec
    style E fill:#e8f5e9
    style F fill:#fff9c4
    style G fill:#ffebee
    style H fill:#ede7f6
    style I fill:#e0f2f1
```

---

## 📋 Casos de Uso

```mermaid
graph TD
    UC1["Generar Boleta<br/>sin firma"]
    UC2["Generar Factura<br/>sin firma"]
    UC3["Generar & Firmar<br/>Boleta"]
    UC4["Generar & Firmar<br/>& Enviar Boleta"]
    UC5["Procesar<br/>Lote de Boletas"]
    UC6["API REST<br/>para Comprobantes"]
    
    Boleta["Clase Boleta"]
    Factura["Clase Factura"]
    Firma["FirmaService"]
    Sunat["SunatService"]
    
    UC1 -->|usa| Boleta
    UC2 -->|usa| Factura
    UC3 -->|usa| Boleta
    UC3 -->|usa| Firma
    UC4 -->|usa| Boleta
    UC4 -->|usa| Firma
    UC4 -->|usa| Sunat
    UC5 -->|usa| Boleta
    UC5 -->|usa| Firma
    UC5 -->|usa| Sunat
    UC6 -->|wrapper| UC4
    
    style UC1 fill:#c8e6c9
    style UC2 fill:#c8e6c9
    style UC3 fill:#fff9c4
    style UC4 fill:#ffccbc
    style UC5 fill:#b3e5fc
    style UC6 fill:#f8bbd0
```

---

## 🏢 Configuración de Ambiente

```mermaid
graph LR
    subgraph Dev["DESARROLLO"]
        Beta["SUNAT BETA<br/>e-beta.sunat.gob.pe<br/>RUC+MODDATOS<br/>moddatos"]
        Dev_Certs["Certificados<br/>de Prueba"]
        Dev_Data["Datos de<br/>Prueba"]
    end
    
    subgraph Prod["PRODUCCIÓN"]
        Prod_URL["SUNAT PROD<br/>e-factura.sunat.gob.pe<br/>Usuario Real<br/>Contraseña Real"]
        Prod_Certs["Certificados<br/>Reales"]
        Prod_Data["Datos<br/>Reales"]
    end
    
    Config["SunatService<br/>ambiente=beta/prod"]
    
    Config -->|conecta a| Beta
    Config -->|o conecta a| Prod_URL
    
    Dev --> Dev_Certs
    Dev --> Dev_Data
    Prod --> Prod_Certs
    Prod --> Prod_Data
```

---

## 📊 Comparación: Antes vs Después

```mermaid
graph TB
    subgraph Antes["❌ ANTES (Monolítico)"]
        A1["sunat_boleta_beta.py<br/>~380 líneas"]
        A2["Constantes globales"]
        A3["Funciones sueltas"]
        A4["Solo Boletas"]
        A5["XML hardcodeado"]
    end
    
    subgraph Después["✅ DESPUÉS (Modular)"]
        D1["src/comprobantes.py<br/>~280 líneas"]
        D2["Clases con datos"]
        D3["Métodos organizados"]
        D4["Boletas + Facturas"]
        D5["XML dinámico"]
        D6["src/firma_envio.py<br/>~330 líneas"]
        D7["Servicios reutilizables"]
    end
    
    style A1 fill:#ffcdd2
    style A2 fill:#ffcdd2
    style A3 fill:#ffcdd2
    style A4 fill:#ffcdd2
    style A5 fill:#ffcdd2
    
    style D1 fill:#c8e6c9
    style D2 fill:#c8e6c9
    style D3 fill:#c8e6c9
    style D4 fill:#c8e6c9
    style D5 fill:#c8e6c9
    style D6 fill:#c8e6c9
    style D7 fill:#c8e6c9
```

---

## 🎯 Capas Lógicas

```mermaid
graph TB
    Layer1["CAPA PRESENTACIÓN<br/>main.py / ejemplo_uso.py<br/>(CLI / Ejemplos)"]
    
    Layer2["CAPA LÓGICA DE NEGOCIO<br/>Boleta / Factura<br/>(Generación de Comprobantes)"]
    
    Layer3["CAPA DE SERVICIOS<br/>FirmaService / ZipService<br/>FileService / SunatService<br/>(Operaciones Técnicas)"]
    
    Layer4["CAPA DE INTEGRACIÓN<br/>Archivos XML/ZIP<br/>SUNAT SOAP<br/>Certificados"]
    
    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    
    style Layer1 fill:#e1f5fe
    style Layer2 fill:#fff9c4
    style Layer3 fill:#f3e5f5
    style Layer4 fill:#fce4ec
```

---

## 📈 Escalabilidad: Agregar Nuevo Tipo

```mermaid
graph LR
    Actual["Boleta<br/>Factura"]
    
    Nuevo1["+ Nota Crédito"]
    Nuevo2["+ Nota Débito"]
    Nuevo3["+ Guía Remisión"]
    
    Futuro["Sistema<br/>Completo"]
    
    Actual --> Nuevo1
    Actual --> Nuevo2
    Actual --> Nuevo3
    
    Nuevo1 --> Futuro
    Nuevo2 --> Futuro
    Nuevo3 --> Futuro
    
    style Actual fill:#c8e6c9
    style Nuevo1 fill:#fff9c4
    style Nuevo2 fill:#fff9c4
    style Nuevo3 fill:#fff9c4
    style Futuro fill:#ffccbc
```

---

## 🔐 Flujo de Seguridad

```mermaid
graph LR
    XML["XML sin firmar"]
    PFX["Certificado PFX<br/>+ Contraseña"]
    KEY["Llave Privada<br/>Extraída"]
    CERT["Certificado<br/>Extraído"]
    SIGN["Firma Digital<br/>RSA-SHA256"]
    SIGNED["XML Firmado<br/>+ Firma en ExtensionContent"]
    
    XML -->|+ | PFX
    PFX -->|Decrypt| KEY
    PFX -->|Extract| CERT
    KEY -->|Sign| SIGN
    CERT -->|Embed| SIGN
    SIGN -->|Append| SIGNED
    
    style XML fill:#fce4ec
    style PFX fill:#ffebee
    style KEY fill:#f3e5f5
    style CERT fill:#e1f5fe
    style SIGN fill:#c8e6c9
    style SIGNED fill:#e8f5e9
```

---

## 📞 Integración con SUNAT

```mermaid
graph LR
    ZIP["Archivo ZIP<br/>con XML Firmado"]
    SOAP["Mensaje SOAP<br/>sendBill"]
    AUTH["Autenticación<br/>Usuario + Contraseña"]
    SEND["Envío HTTP POST"]
    SUNAT["SUNAT<br/>BETA/Producción"]
    RESPONSE["Respuesta SOAP<br/>applicationResponse"]
    CDR["CDR ZIP<br/>Comprimido"]
    EXTRACT["Extraer &<br/>Procesar"]
    
    ZIP --> SOAP
    SOAP --> AUTH
    AUTH --> SEND
    SEND --> SUNAT
    SUNAT --> RESPONSE
    RESPONSE --> CDR
    CDR --> EXTRACT
    
    style ZIP fill:#fce4ec
    style SOAP fill:#f3e5f5
    style AUTH fill:#e1f5fe
    style SEND fill:#fff9c4
    style SUNAT fill:#ffccbc
    style RESPONSE fill:#c8e6c9
    style CDR fill:#e8f5e9
    style EXTRACT fill:#e0f2f1
```

---

## 🚀 Ciclo de Vida de un Comprobante

```mermaid
stateDiagram-v2
    [*] --> Creado: new Boleta()
    
    Creado --> ConLineas: agregar_linea()
    ConLineas --> XMLGenerado: generar_xml()
    
    XMLGenerado --> XMLGuardado: guardar_xml()
    
    XMLGuardado --> Firmado: firmar_xml()
    XMLGuardado --> NoFirmado: (saltado)
    
    Firmado --> ZIPCreado: crear_zip()
    NoFirmado --> ZIPCreado: crear_zip()
    
    ZIPCreado --> Enviado: enviar_sunat()
    ZIPCreado --> NoEnviado: (saltado)
    
    Enviado --> CDRRecibido: procesar_respuesta()
    NoEnviado --> Completado: archivo ZIP
    
    CDRRecibido --> Completado: CDR procesado
    
    Completado --> [*]
```

---

## 📚 Dependencias de Librerías

```mermaid
graph TB
    app["Aplicación SUNAT"]
    
    app -->|XML| lxml["lxml<br/>Procesamiento XML"]
    app -->|Firma| signxml["signxml<br/>Firma XMLDSig"]
    app -->|Criptografía| crypto["cryptography<br/>Manejo de certificados"]
    app -->|SOAP| requests["requests<br/>HTTP POST"]
    
    crypto --> hazmat["hazmat<br/>Primitivas criptográficas"]
    signxml --> lxml
    
    style app fill:#fff9c4
    style lxml fill:#e1f5fe
    style signxml fill:#f3e5f5
    style crypto fill:#ffccbc
    style requests fill:#c8e6c9
    style hazmat fill:#fce4ec
```

---

## 🎓 Patrones de Diseño Utilizados

```mermaid
graph LR
    Strategy["STRATEGY<br/>FirmaService / ZipService<br/>pueden cambiarse"]
    
    Template["TEMPLATE METHOD<br/>Comprobante.generar_xml()<br/>define estructura,<br/>subclases implementan"]
    
    Factory["FACTORY<br/>FileService.generar_nombre_base()<br/>crea nombres]
    
    Composite["COMPOSITE<br/>Comprobante contiene<br/>LineaItems"]
    
    State["STATE<br/>Comprobante: creado,<br/>con_lineas, firmado, enviado"]
    
    style Strategy fill:#fff9c4
    style Template fill:#e1f5fe
    style Factory fill:#c8e6c9
    style Composite fill:#f3e5f5
    style State fill:#ffccbc
```

