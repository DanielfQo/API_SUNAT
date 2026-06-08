# API SUNAT MVP - DB Schema (Compact + Rules)

## Company

```text
id PK
ruc UNIQUE
business_name
created_at
```

## ClientApp

```text
id PK
company_id FK -> Company.id
name
api_key UNIQUE
api_secret
active
created_at
```

## SunatCredential

```text
id PK
company_id FK -> Company.id UNIQUE
sunat_user
sunat_password_encrypted
environment
created_at
```

## ElectronicDocument

```text
id PK
company_id FK -> Company.id
document_type
series
number
customer_document
total_amount
xml_path
zip_path
cdr_zip_path
hash
sunat_ticket
sunat_status
sunat_response JSON
created_at
updated_at
```

UNIQUE:

```text
(company_id, series, number)
```

## Request

```text
id PK
company_id FK -> Company.id
client_app_id FK -> ClientApp.id
electronic_document_id FK -> ElectronicDocument.id NULL
operation
request_payload JSON
response_payload JSON
status
created_at
```

## Relations

```text
Company 1 -> N ClientApp
Company 1 -> 1 SunatCredential
Company 1 -> N ElectronicDocument
Company 1 -> N Request
ClientApp 1 -> N Request
ElectronicDocument 1 -> N Request
```

---

# IMPORTANT RULES (MVP)

## 1. Multi-tenant obligatorio

* TODO debe filtrar por company_id
* Nunca mezclar datos entre empresas

## 2. Seguridad

* api_key identifica ClientApp
* nunca exponer sunat_password sin cifrar
* sunat_password_encrypted obligatorio

## 3. SUNAT flow

* Primero generar XML
* Luego firmar XML
* Luego zip (envío a SUNAT)
* Guardar zip_path
* Guardar ticket si existe
* Guardar respuesta JSON siempre

## 4. Document lifecycle

```text
PENDING -> SENT -> ACCEPTED / REJECTED / ERROR
```

## 5. Request logging obligatorio

* Toda llamada a SUNAT se registra en Request
* request_payload y response_payload siempre guardados
* sirve para auditoría y debugging

## 6. Storage

* XML/ZIP/CDR NO en DB
* solo rutas (paths)
* recomendado: filesystem o S3/MinIO

## 7. Idempotencia

* (company_id, series, number) debe ser único
* evitar duplicar facturas

## 8. ClientApp control

* cada request debe venir de una api_key válida
* Request siempre guarda client_app_id

## 9. SUNAT responses

* guardar response completa en JSON
* no perder errores ni mensajes

## 10. Escalabilidad futura

* esta estructura debe permitir agregar:

  * webhooks
  * billing
  * queues (Celery)
  * retry de envíos
