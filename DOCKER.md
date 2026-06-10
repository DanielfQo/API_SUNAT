# Guía de Ejecución con Docker — API SUNAT

Este documento detalla los pasos necesarios para configurar y ejecutar el proyecto utilizando **Docker** y **Docker Compose**.

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:
1. **Docker Desktop** (versión reciente). [Descargar Docker](https://www.docker.com/products/docker-desktop/)
2. **Docker Compose** (normalmente incluido con Docker Desktop).

---

## Estructura de Docker en el Proyecto

Los archivos de configuración de Docker se encuentran dentro de la carpeta `core/`:
- `core/Dockerfile`: Define la imagen para la aplicación web de Django (Python 3.12-slim).
- `core/docker-compose.yml`: Define los servicios locales: la base de datos PostgreSQL (`db`) y el servidor Django (`web`).
- `core/.dockerignore`: Lista de archivos que no se incluirán en el contexto de construcción de Docker (como entornos virtuales, caché, etc.).

---

## Guía Paso a Paso para la Ejecución

### 1. Preparar el archivo de entorno (`.env`)

El contenedor de Django requiere variables de entorno para funcionar. Debes crear un archivo `.env` dentro de la carpeta `core/` si aún no lo has hecho.

1. Ve a la carpeta `core/`:
   ```bash
   cd core
   ```
2. Copia la plantilla `.env.example` como `.env`:
   - **En Windows (CMD/PowerShell):**
     ```powershell
     copy .env.example .env
     ```
   - **En Linux/macOS:**
     ```bash
     cp .env.example .env
     ```
3. Edita el archivo `core/.env` si es necesario cambiar alguna contraseña o clave de cifrado (`SUNAT_FERNET_KEY`).

---

### 2. Construir e Iniciar los Contenedores

Desde la terminal, asegúrate de estar dentro del directorio `core/` y ejecuta:

```bash
docker compose up --build
```
*(Nota: Si usas una versión antigua de Docker, el comando puede ser `docker-compose up --build`)*

Este comando realizará las siguientes tareas:
1. Descargará la imagen de PostgreSQL 16.
2. Construirá la imagen local de Python para Django instalando los requerimientos de `requirements.txt`.
3. Esperará a que PostgreSQL esté listo y saludable (`healthcheck`).
4. Aplicará las migraciones pendientes en la base de datos de forma automática (`python manage.py migrate`).
5. Iniciará el servidor Gunicorn en el puerto `8000` del contenedor, mapeado al puerto **`8080`** de tu máquina.

---

### 3. Verificar que el Proyecto está Corriendo

Una vez que los contenedores estén levantados, puedes realizar un health check accediendo en tu navegador o mediante `curl`:

- **URL del servicio:** [http://localhost:8080/](http://localhost:8080/)
- **Django Admin:** [http://localhost:8080/admin/](http://localhost:8080/admin/)

---

## Comandos Útiles de Administración

Todos los siguientes comandos se deben ejecutar desde la carpeta `core/` (donde está el archivo `docker-compose.yml`).

### Crear un Superusuario (Django Admin)
Para acceder al panel de administración de Django, necesitas un usuario administrador. Créalo ejecutando:
```bash
docker compose exec web python manage.py createsuperuser
```
Sigue las instrucciones en la consola para ingresar el nombre de usuario, correo y contraseña.

### Ver Logs en tiempo real
Si quieres ver la salida y los logs de tus contenedores:
```bash
docker compose logs -f
```
Para ver solo los logs del contenedor web de Django:
```bash
docker compose logs -f web
```

### Detener los Contenedores
Para detener el entorno sin borrar los datos:
```bash
docker compose down
```

### Detener y Limpiar (Borrar Base de Datos y Volúmenes)
Si deseas reiniciar la base de datos por completo y eliminar los volúmenes persistentes de Docker:
```bash
docker compose down -v
```

### Ejecutar Pruebas (Tests)
Para correr los tests unitarios dentro del entorno de Docker:
```bash
docker compose exec web python manage.py test
```

### Acceder a la Consola de Django (Shell)
Si necesitas ejecutar comandos interactivos de Python en el contexto de la app:
```bash
docker compose exec web python manage.py shell
```


