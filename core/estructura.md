# Estructura del Proyecto — API SUNAT

```
core/                               ← Raíz del proyecto Django
│
├── manage.py                       ← Entry point CLI (apunta a config.settings.local)
├── requirements.txt                ← Dependencias Python
├── Dockerfile                      ← Imagen Docker (Python 3.12-slim)
├── docker-compose.yml              ← Stack local: web + postgres
├── .env                            ← Variables de entorno (NO commitear)
├── .env.example                    ← Plantilla de variables
├── .gitignore
│
├── config/                         ← Configuración del proyecto Django
│   ├── __init__.py
│   ├── urls.py                     ← URL raíz (conecta todas las apps)
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py                 ← Settings comunes (DB, DRF, Apps, CORS)
│       ├── local.py                ← DEBUG=True, BrowsableAPI, CORS abierto
│       └── production.py          ← DEBUG=False, solo JSONRenderer
│
├── common/                         ← Utilidades compartidas (no es una app Django)
│   ├── __init__.py
│   ├── models.py                   ← Mixins: UUIDPrimaryKeyMixin, TimestampMixin
│   ├── authentication.py           ← ApiKeyAuthentication (header X-API-Key)
│   ├── permissions.py              ← HasValidApiKey (verifica request.auth)
│   └── encryption.py              ← Cifrado Fernet para credenciales SUNAT
│
├── apps/                           ← Apps Django del dominio
│   ├── __init__.py
│   │
│   ├── companies/                  ← Entidad: Company (tenant)
│   │   ├── models.py               → Company (ruc, business_name, is_active)
│   │   ├── serializers.py
│   │   ├── views.py                → CompanyViewSet (CRUD)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── client_apps/                ← Entidad: ClientApp (API consumer)
│   │   ├── models.py               → ClientApp (api_key, api_secret auto-generados)
│   │   ├── serializers.py          → Read / CreateSerializer (secret solo en create)
│   │   ├── views.py                → ClientAppViewSet (CRUD)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── credentials/                ← Entidad: SunatCredential (1:1 con Company)
│   │   ├── models.py               → SunatCredential (password cifrado, env BETA/PROD)
│   │   ├── serializers.py          → Read / WriteSerializer (cifrado Fernet en write)
│   │   ├── views.py                → SunatCredentialViewSet (CRUD)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── documents/                  ← Entidad: ElectronicDocument
│   │   ├── models.py               → ElectronicDocument (factura, boleta, etc.)
│   │   ├── serializers.py
│   │   ├── views.py                → ElectronicDocumentViewSet (CRUD + filtros)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   ├── requests_log/               ← Entidad: RequestLog (audit trail)
│   │   ├── models.py               → RequestLog (inmutable — solo list/retrieve)
│   │   ├── serializers.py
│   │   ├── views.py                → RequestLogViewSet (read-only + filtros)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── apps.py
│   │
│   └── sunat/                      ← Integración con SUNAT (lógica de negocio)
│       ├── models.py               → (vacío — sin modelos propios)
│       ├── services.py             → SunatService (placeholders: send, ticket, CDR)
│       ├── views.py                → SunatSendDocumentView, CheckTicketView, StatusView
│       ├── urls.py                 → /api/sunat/send/, /api/sunat/ticket/<n>/, /api/sunat/status/
│       ├── admin.py
│       └── apps.py
│
├── certs/                          ← Certificados digitales
│   └── certificado.pfx
│
└── storage/                        ← Archivos generados (no commitear contenido)
    └── companies/                  ← (futuro: xml/, zip/, cdr/ por empresa)
```

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Health check |
| `*` | `/admin/` | Django Admin |
| GET/POST | `/api/companies/` | Listar / Crear empresas |
| GET/PUT/DELETE | `/api/companies/{id}/` | Detalle empresa |
| GET/POST | `/api/client-apps/` | Listar / Crear apps cliente |
| GET/PUT/DELETE | `/api/client-apps/{id}/` | Detalle app cliente |
| GET/POST | `/api/credentials/` | Listar / Crear credenciales SUNAT |
| GET/PUT/DELETE | `/api/credentials/{id}/` | Detalle credencial |
| GET/POST | `/api/documents/` | Listar / Crear documentos electrónicos |
| GET/PUT/DELETE | `/api/documents/{id}/` | Detalle documento |
| GET | `/api/request-logs/` | Listar logs (solo lectura) |
| GET | `/api/request-logs/{id}/` | Detalle log |
| POST | `/api/sunat/send/` | Enviar comprobante a SUNAT (pendiente) |
| GET | `/api/sunat/ticket/{n}/` | Consultar ticket SUNAT (pendiente) |
| GET | `/api/sunat/status/` | Estado conexión SUNAT (pendiente) |

## Autenticación

Todos los endpoints (excepto `/`, `/admin/`, `/api/sunat/status/`) requieren el header:

```
X-API-Key: <api_key>
```

La `api_key` se obtiene al crear un `ClientApp`.

## Variables de Entorno Requeridas

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Secret key de Django |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario PostgreSQL |
| `DB_PASSWORD` | Contraseña PostgreSQL |
| `DB_HOST` | Host de PostgreSQL (`db` en Docker) |
| `DB_PORT` | Puerto PostgreSQL (default: 5432) |
| `SUNAT_FERNET_KEY` | Clave Fernet para cifrar credenciales SUNAT |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos para CORS |