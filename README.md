# BioGestor Backend

API backend de BioGestor, desarrollado con Django y Django REST Framework. PostgreSQL es la base de datos de persistencia y Amazon S3 será el almacenamiento de los archivos de datasets cuando se implemente ese módulo.

## Stack inicial

- Python 3.13.
- Django 5.2.17.
- Django REST Framework 3.18.3.
- PostgreSQL mediante Psycopg 3.
- Configuración local desde variables de entorno.
- Pruebas con el test runner de Django, cobertura con Coverage.py y estilo con Ruff.

Django 5.2 es una versión LTS. Las versiones de dependencias están fijadas en requirements.txt para que las instalaciones del equipo sean reproducibles; se deben revisar actualizaciones de seguridad de forma periódica.

## Estructura del proyecto

~~~text
.
├── apps/
│   ├── audit/          # Auditoría funcional
│   ├── core/           # Funciones transversales y health check
│   ├── datasets/       # Catálogo y versiones de datasets
│   ├── experiments/    # Experimentos y resultados
│   ├── identity/       # Identidad, usuarios y acceso
│   ├── integrations/   # Integración con BioDynamics
│   ├── ml_models/      # Modelos y versiones de ML
│   ├── observations/   # Comentarios y observaciones
│   └── storage/        # Referencias y acceso a archivos
├── config/             # Configuración Django, URLs, ASGI y WSGI
├── .dockerignore       # Archivos excluidos de la imagen de Docker
├── .env.example        # Variables de ejemplo; no contiene secretos reales
├── Dockerfile          # Imagen del backend para desarrollo local
├── compose.yaml        # Backend y PostgreSQL para desarrollo local
├── manage.py
├── requirements.txt
└── requirements-dev.txt
~~~

Los módulos de dominio se dejan preparados como aplicaciones Django; sus modelos y reglas de negocio se implementarán en tareas posteriores. En esta tarea solo se implementa el endpoint transversal de comprobación de estado.

## Requisitos previos

- Python 3.13.
- Docker Engine y Docker Compose, o una instalación local de PostgreSQL compatible.
- Git.

## Instalación y ejecución local

### 1. Clonar el repositorio

~~~bash
git clone https://github.com/m-alvaradox/biogestor-backend.git
cd biogestor-backend
git switch develop
~~~

No hace falta instalar Python ni PostgreSQL: el backend y la base de datos se ejecutan en contenedores con Docker.

### 2. Configurar el entorno

~~~bash
cp .env.example .env
~~~

En Windows PowerShell, copia el archivo con:

~~~powershell
Copy-Item .env.example .env
~~~

Edita .env y coloca una clave de desarrollo propia y una contraseña local para PostgreSQL. El archivo .env se ignora desde Git y no debe subirse al repositorio.

### 3. Iniciar PostgreSQL y el backend

~~~bash
docker compose up --build -d
docker compose ps
~~~

La configuración expone PostgreSQL únicamente en la interfaz local, en el puerto indicado por POSTGRES_PORT (5432 por defecto). Dentro de Docker, el backend se conecta al servicio `db`: POSTGRES_HOST se sobrescribe a `db`, por lo que el valor de .env solo aplica si ejecutas Django fuera de Docker.

### 4. Validar y preparar la base de datos

~~~bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexión OK')"
~~~

Si se imprime `Conexión OK` y las migraciones se aplican, el backend se conecta correctamente a PostgreSQL.

Las migraciones iniciales corresponden a las aplicaciones integradas de Django. Todavía no se han definido modelos de negocio de BioGestor, por lo que no se crean tablas de datasets, modelos ni experimentos en esta tarea.

### 5. Acceder al backend

El backend queda disponible en http://127.0.0.1:8000/ con el servidor de desarrollo de Django. No se debe usar runserver como servidor de producción.

Para ver los registros del backend o detener el entorno:

~~~bash
docker compose logs -f backend
docker compose down        # conserva los datos; con -v también los elimina
~~~

## Endpoint de estado

~~~http
GET /api/v1/health/
~~~

Respuesta esperada (HTTP 200):

~~~json
{
  "status": "ok",
  "service": "biogestor-backend"
}
~~~

Este endpoint comprueba que la aplicación HTTP está respondiendo. No verifica todavía la conectividad con PostgreSQL, S3 ni BioDynamics; esas comprobaciones se añadirán cuando se definan las necesidades de disponibilidad y despliegue.

Ejemplo desde terminal:

~~~bash
curl -i http://127.0.0.1:8000/api/v1/health/
~~~

En Windows PowerShell usa `curl.exe` en lugar de `curl`.

Las solicitudes POST y otros métodos no admitidos reciben HTTP 405 Method Not Allowed.

## Pruebas y calidad

~~~bash
docker compose exec backend python manage.py test
docker compose exec backend coverage run manage.py test
docker compose exec backend coverage report --fail-under=70
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
~~~

La integración continua ejecuta comprobaciones de Django, pruebas, cobertura mínima del 70 % para el módulo core del endpoint y comprobaciones de Ruff. Las pruebas del health check no requieren que PostgreSQL esté disponible; ejecutar migraciones sí requiere una base de datos activa.

## Variables de entorno

| Variable | Propósito |
| --- | --- |
| DJANGO_SECRET_KEY | Clave criptográfica de Django; no reutilizar la clave de ejemplo en producción. |
| DJANGO_DEBUG | Activa o desactiva el modo de depuración. |
| DJANGO_ALLOWED_HOSTS | Lista de hosts permitidos, separados por comas. |
| POSTGRES_DB | Nombre de la base de datos. |
| POSTGRES_USER | Usuario de PostgreSQL. |
| POSTGRES_PASSWORD | Contraseña local de PostgreSQL. |
| POSTGRES_HOST | Host de PostgreSQL desde el proceso Django. |
| POSTGRES_PORT | Puerto de PostgreSQL. |

En un entorno que no sea de desarrollo debe configurarse una clave segura, deshabilitar DJANGO_DEBUG y ajustar los hosts permitidos.

## Alcance de esta inicialización

Incluye el proyecto Django, la estructura modular base, variables de entorno de ejemplo, configuración de PostgreSQL, endpoint de estado, pruebas automatizadas y documentación de ejecución. No incluye todavía modelos de dominio, autenticación de BioGestor, autorización por roles, integración real con S3, contrato de ingesta de BioDynamics ni despliegue de producción.
