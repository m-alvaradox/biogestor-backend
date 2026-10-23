# BioGestor Backend

API backend de BioGestor, desarrollado con Django y Django REST Framework. PostgreSQL es la base de datos de persistencia y Amazon S3 será el almacenamiento de los archivos de datasets cuando se implemente ese módulo.

Estado actual: ya están implementados los endpoints de estado, la **identidad de usuarios con cinco roles y matriz de permisos** (`apps/identity`) y el **modelo base del catálogo de datasets** (`apps/datasets`). El resto de módulos de dominio sigue como estructura preparada.

## Stack inicial

- Python 3.13.
- Django 5.2.17.
- Django REST Framework 3.18.3, con autenticación por token (`rest_framework.authtoken`).
- PostgreSQL mediante Psycopg 3.
- Configuración local desde variables de entorno.
- Pruebas con el test runner de Django, cobertura con Coverage.py y estilo con Ruff.

Django 5.2 es una versión LTS. Las versiones de dependencias están fijadas en requirements.txt para que las instalaciones del equipo sean reproducibles; se deben revisar actualizaciones de seguridad de forma periódica.

## Estructura del proyecto

~~~text
.
├── apps/
│   ├── audit/          # Auditoría funcional (pendiente)
│   ├── core/           # Funciones transversales y health checks
│   ├── datasets/       # Catálogo de datasets (modelo Dataset implementado; versiones pendientes)
│   ├── experiments/    # Experimentos y resultados (pendiente)
│   ├── identity/       # Usuarios, roles, login y matriz de permisos
│   ├── integrations/   # Integración con BioDynamics (pendiente)
│   ├── ml_models/      # Modelos y versiones de ML (pendiente)
│   ├── observations/   # Comentarios y observaciones (pendiente)
│   └── storage/        # Referencias y acceso a archivos (pendiente)
├── config/             # Configuración Django, URLs, ASGI y WSGI
├── .dockerignore       # Archivos excluidos de la imagen de Docker
├── .env.example        # Variables de ejemplo; no contiene secretos reales
├── Dockerfile          # Imagen del backend para desarrollo local
├── compose.yaml        # Backend y PostgreSQL para desarrollo local
├── manage.py
├── requirements.txt
└── requirements-dev.txt
~~~

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

- Al inicializar la base de datos por primera vez (por ejemplo, tras clonar el repositorio o después de `docker compose down -v`, que elimina los datos).
- Cuando existan nuevas migraciones pendientes, por ejemplo después de actualizar la rama con cambios que incluyan migraciones.

Django registra las migraciones ya aplicadas, por lo que volver a ejecutar `migrate` cuando no hay pendientes no modifica la base de datos.

Las migraciones corresponden a las aplicaciones integradas de Django, `apps/core` (`IntegrationProbe`, modelo técnico de las pruebas de integración), `apps/identity` (`Usuario`) y `apps/datasets` (`Dataset`).

> **Importante:** el proyecto usa un modelo de usuario propio (`AUTH_USER_MODEL = "identity.Usuario"`). Si tu base local se migró antes de que existiera `apps/identity`, las tablas de usuarios quedaron con el modelo por defecto de Django y las migraciones fallarán. Reinicia la base con `docker compose down -v` y vuelve a ejecutar `migrate`.

### 5. Crear el primer Administrador

~~~bash
docker compose exec backend python manage.py createsuperuser
~~~

El superusuario se crea con el rol **Administrador** y puede crear a los demás usuarios desde la API (`/usuarios/`) o desde el panel de Django (`/admin/`).

### 6. Acceder al backend

El backend queda disponible en http://127.0.0.1:8080/ con el servidor de desarrollo de Django (`compose.yaml` publica el puerto 8000 del contenedor en el 8080 local). No se debe usar runserver como servidor de producción.

Para ver los registros del backend o detener el entorno:

~~~bash
docker compose logs -f backend
docker compose down        # conserva los datos; con -v también los elimina
~~~

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

## Identidad, roles y permisos

El módulo `apps/identity` define el modelo `Usuario` (extiende `AbstractUser`) con correo único, `rol` y `departamento`. El estado activo/inactivo usa el campo `is_active` de Django. El rol vive en BioGestor y no en el proveedor de login, para que un futuro inicio de sesión con cuentas de BioDynamics no cambie los permisos.

### Roles

| Valor | Nombre |
| --- | --- |
| `administrador` | Administrador |
| `product_owner` | Product Owner |
| `ingeniero_datos` | Ingeniero de Datos |
| `ml_operator` | Machine Learning Operator |
| `cientifico_datos` | Científico de Datos |

El rol por defecto de un usuario nuevo es `cientifico_datos`, el de menos permisos.

### Matriz de permisos

La matriz está definida en un único archivo, `apps/identity/permisos.py`; las vistas solo declaran qué operación realizan. No existe una operación para modificar la auditoría: nadie puede hacerlo.

| Operación | Admin | PO | Ing. Datos | ML Operator | Científico |
| --- | :-: | :-: | :-: | :-: | :-: |
| Consultar datasets | ✓ | ✓ | ✓ | ✓ | ✓ |
| Consultar modelos y versiones | ✓ | ✓ | ✓ | ✓ | ✓ |
| Comparar modelos | ✓ | ✓ | ✓ | ✓ | ✓ |
| Registrar observaciones | ✓ | ✓ | ✓ | ✓ | ✓ |
| Registrar datasets | ✓ |  | ✓ |  |  |
| Modificar metadatos | ✓ |  | ✓ |  |  |
| Registrar versiones de modelos | ✓ |  | ✓ |  |  |
| Monitorear integración API | ✓ |  | ✓ |  |  |
| Configurar almacenamiento | ✓ |  | ✓ |  |  |
| Aprobar o rechazar modelos | ✓ | ✓ |  |  |  |
| Cambiar estado de modelos | ✓ | ✓ |  |  |  |
| Ejecutar o solicitar pruebas | ✓ | ✓ |  | ✓ |  |
| Consultar auditoría | ✓ | ✓ | ✓ |  |  |
| Gestionar usuarios y roles | ✓ |  |  |  |  |

Decisiones pendientes de confirmar con el Product Owner (anotadas en `permisos.py`):

- El alcance del permiso «Limitado» del Ingeniero de Datos sobre el cambio de estado de modelos.
- Quién puede registrar observaciones: hoy se permite a todos los roles (RF-14 / HU-09).
- Qué registros de auditoría ve cada rol: el filtro se aplicará en la vista de auditoría.

### Cómo proteger una vista

~~~python
from apps.identity.permisos import Operacion, PermisoPorMetodo, requiere

# Una sola operación
permission_classes = [requiere(Operacion.GESTIONAR_USUARIOS)]

# Operación distinta según el método HTTP
permission_classes = [PermisoPorMetodo]
operaciones = {
    "GET": Operacion.CONSULTAR_DATASETS,
    "POST": Operacion.REGISTRAR_DATASETS,
    "PATCH": Operacion.MODIFICAR_METADATOS,
}
~~~

Un método HTTP que no esté declarado en `operaciones` se rechaza. `HEAD` y `OPTIONS` se tratan como `GET`.

## Endpoints de autenticación y usuarios

La autenticación usa tokens de DRF: después del login se envía el encabezado `Authorization: Token <token>`.

| Método | Ruta | Descripción | Acceso |
| --- | --- | --- | --- |
| POST | `auth/login/` | Recibe `username` y `password`; devuelve `token` y el perfil. | Público |
| POST | `auth/logout/` | Borra el token del usuario (HTTP 204). | Autenticado |
| GET | `auth/perfil/` | Perfil del usuario autenticado, con su lista de `operaciones` permitidas. | Autenticado |
| GET, POST | `usuarios/` | Lista (filtros `rol` y `departamento`) y crea usuarios. | Administrador |
| GET, PUT, PATCH, DELETE | `usuarios/<id>/` | Detalle, edición y baja de un usuario. | Administrador |

Detalles de comportamiento:

- Credenciales incorrectas o cuenta inactiva devuelven **HTTP 400** con `{"detail": "Usuario o contraseña incorrectos."}`.
- Un login repetido reutiliza el mismo token.
- `DELETE /usuarios/<id>/` **no borra** al usuario: lo desactiva (`is_active = false`) y revoca su token, porque puede ser propietario de datasets y aparecer en la auditoría.
- La contraseña se guarda cifrada, tiene mínimo 8 caracteres, es obligatoria al crear y opcional al editar. Nunca se devuelve en las respuestas.
- El perfil es de solo lectura; un usuario no puede cambiar su propio rol.
- `operaciones` en el perfil permite al frontend mostrar u ocultar botones. La autorización real siempre se valida en el backend.

~~~bash
# Iniciar sesión
curl -X POST http://127.0.0.1:8080/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "ClaveSegura123"}'

# Usar el token
curl http://127.0.0.1:8080/api/v1/auth/perfil/ \
  -H "Authorization: Token <token>"
~~~

## Catálogo de datasets

El modelo `Dataset` (`apps/datasets`) representa un conjunto de datos registrado. **BioGestor no sube ni copia archivos**: solo guarda la referencia a un objeto o carpeta que ya existe en S3, más su metadata.

- **Obligatorios:** `nombre` y `tipo` (`audio`, `imagen`, `video`, `csv`, `texto`, `otro`).
- **Listado:** `propietario` (investigador responsable, `PROTECT`), `estado` (`activo`, `procesando`, `archivado`, `error`), `fecha_registro`, `fecha_actualizacion`.
- **Metadatos:** `descripcion`, `especie`, `granja`, `piscina`, `fecha_captura`, `licencia` y `metadatos_tipo` (JSON para campos que dependen del tipo, como micrófono o frecuencia de muestreo).
- **Almacenamiento:** `ubicacion_s3`, `formato`, `tamano_bytes`, `cantidad_archivos`.

Restricciones en PostgreSQL:

- `ubicacion_s3` debe empezar con `s3://` (o estar vacía mientras no se conozca).
- La misma `ubicacion_s3` no puede registrarse dos veces; varios datasets sin referencia sí son válidos.
- `fecha_captura` no puede ser futura.

Todavía no hay endpoints de datasets, ni la separación `Dataset` / `DatasetVersion` definida en el modelo de datos preliminar. Ambos se implementarán en tareas posteriores.

## Pruebas y calidad

~~~bash
docker compose exec backend python manage.py test
docker compose exec backend coverage run manage.py test
docker compose exec backend coverage report --fail-under=70
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
~~~

Las pruebas de los health checks no requieren que PostgreSQL esté disponible (la caída de la base se simula); ejecutar migraciones y las pruebas de modelos sí requiere una base de datos activa.

Para ejecutar solo un módulo:

~~~bash
docker compose exec backend python manage.py test apps.identity
docker compose exec backend python manage.py test apps.datasets
~~~

Las pruebas de `identity` cubren el modelo, la matriz de permisos por rol, las clases de permiso de DRF, login, logout, perfil y el CRUD de usuarios con sus filtros.

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

## Contribución

Las ramas, commits, Pull Requests y revisiones siguen [CONTRIBUTING.md](CONTRIBUTING.md). En resumen: se trabaja desde `develop` con ramas `feature/*`, `fix/*` y `chore/*`; no hay push directo a `main` ni `develop`; cada PR necesita aprobación de otro integrante y del CODEOWNER, y los endpoints nuevos llevan pruebas automatizadas.

## Alcance actual y pendientes

**Incluye:** proyecto Django, estructura modular, variables de entorno de ejemplo, configuración de PostgreSQL, endpoints de estado, autenticación por token, usuarios con cinco roles, matriz de permisos, modelo `Dataset` con sus restricciones, pruebas automatizadas y documentación de ejecución.

**No incluye todavía:**

- Endpoints del catálogo de datasets y separación `Dataset` / `DatasetVersion`.
- Modelos, versiones, experimentos, observaciones y auditoría.
- Integración real con S3.
- Contrato de ingesta de BioDynamics y autorización del servicio que envía resultados.
- Inicio de sesión con cuentas de BioDynamics (el rol ya vive en `Usuario` para facilitarlo).
- Despliegue de producción.