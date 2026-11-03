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
│   ├── core/           # Funciones transversales y health checks
│   ├── datasets/       # Catálogo de datasets (modelo Dataset) y comando seed_data
│   ├── experiments/    # Experimentos y resultados
│   ├── integrations/   # Integración con BioDynamics
│   ├── ml_models/      # Modelos y versiones de ML
│   ├── observations/   # Comentarios y observaciones
│   ├── storage/        # Referencias y acceso a archivos
│   └── users/          # Usuarios según el diagrama de clases (modelo User)
├── config/             # Configuración Django, URLs, ASGI y WSGI
├── docs/               # Guías del equipo (datos semilla)
├── .dockerignore       # Archivos excluidos de la imagen de Docker
├── .env.example        # Variables de ejemplo; no contiene secretos reales
├── Dockerfile          # Imagen del backend para desarrollo local
├── compose.yaml        # Backend y PostgreSQL para desarrollo local
├── manage.py
├── requirements.txt
└── requirements-dev.txt
~~~

Los módulos de dominio se dejan preparados como aplicaciones Django y sus modelos se implementan por tareas. Ya están implementados `users` (modelo `User`) y `datasets` (modelo `Dataset`), además de los endpoints transversales de comprobación de estado de la aplicación y de la base de datos. El resto de módulos se implementará en tareas posteriores.

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

Si se imprime `Conexión OK` y las migraciones se aplican, el backend se conecta correctamente a PostgreSQL. También puedes comprobarlo con `GET /api/v1/health/db/` (ver "Endpoints de estado").

El comando `migrate` se ejecuta de forma manual y no es necesario después de cada inicio de los contenedores. Debe ejecutarse:

- Al inicializar la base de datos por primera vez (por ejemplo, tras clonar el repositorio).
- Cuando existan nuevas migraciones pendientes, por ejemplo después de actualizar la rama con cambios que incluyan migraciones.

Django registra las migraciones ya aplicadas, por lo que volver a ejecutar `migrate` cuando no hay pendientes no modifica la base de datos.

Las migraciones incluyen las aplicaciones integradas de Django, `apps/core` (`0001_initial`, con el modelo técnico `IntegrationProbe` usado en las pruebas de integración), `apps/users` (`0001_initial`, tabla de usuarios) y `apps/datasets` (`0001_initial`, tabla de datasets). `datasets` depende de `users`, y Django las aplica en ese orden.

### 5. Acceder al backend

El backend queda disponible en http://127.0.0.1:8080/ con el servidor de desarrollo de Django (`compose.yaml` publica el puerto 8000 del contenedor en el 8080 local). No se debe usar runserver como servidor de producción.

Para ver los registros del backend o detener el entorno:

~~~bash
docker compose logs -f backend
docker compose down        # detiene los contenedores y conserva los datos
~~~

No uses `docker compose down -v` como solución general: elimina el volumen de PostgreSQL y todos sus datos.

## Datos semilla para desarrollo

El comando `seed_data` puebla la base local con datos ficticios para que Frontend y Backend prueben contra la misma información. Siembra usuarios y datasets; las versiones, los modelos de ML, los experimentos y las observaciones se siembran cuando existan sus modelos (mientras tanto se omiten con una advertencia).

~~~bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_data
~~~

- Es idempotente: ejecutarlo varias veces no genera duplicados.
- Solo se ejecuta con `DJANGO_DEBUG` activo; con `DEBUG=False` se niega, salvo que se use `--force`.
- No incluye credenciales ni datos reales: los correos son `@example.com` y las referencias S3 apuntan a `s3://biogestor-seed/`.

Detalle de los datos incluidos, verificación y cómo agregar entidades: [docs/SEED_DATA.md](docs/seed_data.md).

## Endpoints de estado

### Estado de la aplicación

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

Este endpoint solo comprueba que la aplicación HTTP está respondiendo. **No consulta PostgreSQL, a propósito**: el CI lo usa para verificar la imagen Docker sin base de datos.

### Estado de la base de datos

~~~http
GET /api/v1/health/db/
~~~

Ejecuta una consulta mínima (`SELECT 1`) contra PostgreSQL.

- **HTTP 200** si la base de datos responde.
- **HTTP 503 Service Unavailable** si no se puede conectar o consultar.

Aún no verifica S3 ni BioDynamics; esas comprobaciones se añadirán cuando se definan las necesidades de disponibilidad y despliegue.

### Ejemplos desde terminal

~~~bash
curl -i http://127.0.0.1:8080/api/v1/health/
curl -i http://127.0.0.1:8080/api/v1/health/db/
~~~

En Windows PowerShell usa `curl.exe` en lugar de `curl`.

Para ver el 503, detén la base con `docker compose stop db`, repite la petición y vuelve a iniciarla con `docker compose start db`.

Las solicitudes POST y otros métodos no admitidos reciben HTTP 405 Method Not Allowed.

## Catálogo de datasets

~~~http
GET /api/v1/datasets/
~~~

Lista los datasets registrados en PostgreSQL, paginados y ordenados del más reciente al más antiguo. Por ahora no requiere autenticación; se protegerá cuando exista el login de BioGestor.

| Parámetro | Descripción |
| --- | --- |
| `page` | Número de página (por defecto 1). Una página inexistente responde 404. |
| `page_size` | Resultados por página (por defecto 10, máximo 100). |
| `search` | Busca en nombre, descripción y especie, sin distinguir mayúsculas. |
| `type` | `audio`, `image`, `video`, `csv`, `text` u `other`. |
| `status` | `active`, `processing`, `archived` o `error`. |
| `owner` | Id del responsable. |
| `ordering` | `name`, `created_at`, `capture_date` o `type`; con `-` delante es descendente. Por defecto `-created_at`. |

Todos los parámetros son opcionales y se pueden combinar. Un valor no válido en `type`, `status` u `owner` responde HTTP 400 indicando el parámetro.

Respuesta (HTTP 200):

~~~json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Cantos de aves",
      "type": "audio",
      "status": "active",
      "owner": { "id": 3, "name": "Ana Pérez" },
      "created_at": "2026-10-20T15:30:00Z"
    }
  ]
}
~~~

`owner` es el usuario responsable (`id` y `name`) o `null` si el dataset no tiene uno.

~~~bash
curl -i http://127.0.0.1:8080/api/v1/datasets/
curl -i "http://127.0.0.1:8080/api/v1/datasets/?type=audio&ordering=name&page_size=5"
curl -i "http://127.0.0.1:8080/api/v1/datasets/?search=camaron"
~~~

## Detalle de dataset

~~~http
GET /api/v1/datasets/<id>/
~~~

Devuelve un dataset con los campos del catálogo más su metadata y su almacenamiento. Por ahora no requiere autenticación, igual que el catálogo. Un id inexistente responde HTTP 404 y los métodos distintos de GET responden HTTP 405.

Respuesta (HTTP 200):

~~~json
{
  "id": 5,
  "name": "Lote de audio de tilapia 001",
  "type": "audio",
  "status": "active",
  "owner": { "id": 2, "name": "Dra. Ana Lima" },
  "created_at": "2026-10-28T22:51:18.551016-05:00",
  "species": "Tilapia (Oreochromis niloticus)",
  "farm": "Aquamar Norte",
  "pool": "Piscina A-3",
  "capture_date": "2024-10-12",
  "type_metadata": { "microphone": "Hidrófono DolphinEar DE200", "sample_rate": 44100 },
  "storage": {
    "s3_uri": "s3://biogestor-data/tilapia/audio/batch-001/",
    "file_format": ".WAV",
    "size_bytes": 4700000000,
    "file_count": 1247
  }
}
~~~

- `type_metadata` es un JSON libre con los datos propios del tipo (micrófono, frecuencia de muestreo, resolución...).
- `storage` agrupa la referencia al archivo en S3. `size_bytes` está en bytes y `file_format` incluye el punto (`.WAV`). Cuando exista el versionado de datasets, `storage` corresponderá a la versión más reciente.
- Los campos opcionales sin valor se devuelven como `null`.

~~~bash
curl -i http://127.0.0.1:8080/api/v1/datasets/1/
curl -i http://127.0.0.1:8080/api/v1/datasets/999999/
~~~

## Modelos de dominio

### Dataset (`apps/datasets`)

Representa un conjunto de datos registrado en BioGestor. **BioGestor no sube ni copia archivos**: solo guarda la referencia a un objeto o carpeta que ya existe en S3, junto con su metadata.

| Campo | Tipo | Obligatorio | Regla |
| --- | --- | --- | --- |
| `name` | texto (150) | sí | |
| `type` | `DatasetType` | sí | audio, image, video, csv, text, other |
| `status` | `Status` | no | active (por defecto), processing, archived, error |
| `owner` | → `users.User` | no | no se puede borrar un usuario que tiene datasets |
| `capture_date` | fecha | no | si se registra, no puede ser futura |
| `s3_uri` | texto (1024) | no | no se puede repetir la misma referencia |
| `farm`, `pool`, `species`, `license`, `description` | texto | no | |
| `file_format`, `size_bytes`, `file_count`, `type_metadata` | varios | no | `type_metadata` guarda datos propios de cada tipo (JSON) |
| `created_at`, `updated_at` | fecha y hora | automáticos | |

La fecha de captura y la referencia única de S3 se validan con `full_clean()` y también como restricciones en PostgreSQL. Django no ejecuta `full_clean()` al llamar a `save()`, por lo que los formularios y la futura API deben llamarlo antes de guardar.

### User (`apps/users`)

Usuario según el diagrama de clases. Es un modelo de dominio: **no** reemplaza el usuario de autenticación de Django (`AUTH_USER_MODEL`) ni incluye login, permisos o endpoints; eso corresponde a otra tarea.

| Campo | Tipo | Obligatorio | Regla |
| --- | --- | --- | --- |
| `name` | texto (150) | sí | |
| `email` | correo | sí | único |
| `role` | `UserRole` | no | por ahora solo `administrator` (por defecto) |
| `dept` | texto (100) | no | |
| `status` | `UserStatus` | no | active (por defecto), inactive |

## Pruebas y calidad

~~~bash
docker compose exec backend python manage.py test
docker compose exec backend coverage run manage.py test
docker compose exec backend coverage report --fail-under=70
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
~~~

Las pruebas de los health checks no requieren que PostgreSQL esté disponible (la caída de la base se simula); ejecutar migraciones sí requiere una base de datos activa. Las pruebas de `users` y `datasets` usan la base temporal que crea el test runner de Django.

## Integración continua

El flujo `.github/workflows/ci.yml` se ejecuta con GitHub Actions en cada Pull Request y push hacia `develop` o `main`, y también puede lanzarse manualmente desde la pestaña Actions (`workflow_dispatch`). Tiene dos jobs:

1. **Instalación, verificación y pruebas** (con un servicio PostgreSQL 17):
   - Instala las dependencias de `requirements-dev.txt` con Python 3.13 (versión tomada de `.python-version`).
   - Ejecuta `ruff check` y `ruff format --check`.
   - Compila las fuentes con `python -m compileall`.
   - Ejecuta `python manage.py check` y verifica que no falten migraciones (`makemigrations --check --dry-run`).
   - Aplica las migraciones sobre una base de datos PostgreSQL limpia.
   - Ejecuta las pruebas con Coverage.py y exige una cobertura mínima del 70 %.
2. **Compilación de imagen Docker** (solo si el job anterior pasa):
   - Construye la imagen a partir del `Dockerfile`.
   - Ejecuta `python manage.py check` dentro de la imagen.
   - Levanta el backend con Gunicorn, sin base de datos, y comprueba que `GET /api/v1/health/` responda.

Las credenciales del workflow son exclusivas de CI y no se deben reutilizar en otros entornos. Se recomienda configurar ambos jobs como comprobaciones obligatorias en la protección de las ramas `develop` y `main`.

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

## Alcance actual

Incluye el proyecto Django, la estructura modular base, variables de entorno de ejemplo, configuración de PostgreSQL, endpoints de estado de la aplicación y de la base de datos, los modelos de dominio `User` y `Dataset` con sus migraciones, el endpoint de catálogo de datasets, el comando `seed_data` de datos semilla de desarrollo, pruebas automatizadas y documentación de ejecución. No incluye todavía el resto de modelos de dominio, autenticación de BioGestor, autorización por roles, integración real con S3, contrato de ingesta de BioDynamics ni despliegue de producción.
