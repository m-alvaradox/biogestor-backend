# Datos semilla de desarrollo

Comando de Django que puebla la base de datos local con datos **ficticios** de BioGestor,
para que todo el equipo (Frontend y Backend) pruebe contra la misma información.

## Preparación

Con PostgreSQL y backend activos:

~~~bash
docker compose up -d
docker compose exec backend python manage.py migrate
~~~

`migrate` solo hace falta la primera vez o cuando haya migraciones pendientes.

## Ejecución

~~~bash
docker compose exec backend python manage.py seed_data
~~~

Salida con los modelos que existen hoy (`users` y `datasets`):

~~~text
usuarios: 4 creados, 0 ya existían
datasets: 6 creados, 0 ya existían
versiones de dataset: omitido (el modelo aún no existe)
modelos: omitido (el modelo aún no existe)
versiones de modelo: omitido (el modelo aún no existe)
modelo-dataset (versiones): omitido (el modelo aún no existe)
experimentos: omitido (el modelo aún no existe)
observaciones: omitido (el modelo aún no existe)
Datos semilla cargados.
~~~

Al ejecutarlo de nuevo, las entidades sembradas muestran `0 creados`.

Fuera de Docker: `python manage.py seed_data`.

## Reglas del comando

- **Idempotente:** cada registro se identifica por una clave natural y se crea con `get_or_create` o `update_or_create`. Ejecutarlo varias veces no genera duplicados.
- **Transaccional:** si algo falla, no queda ningún dato a medias.
- **Solo desarrollo:** con `DEBUG=False` se niega a ejecutarse, salvo que se use `--force`. No usarlo contra una base compartida o de producción.
- **Sin información sensible:** correos `@example.com`, referencias `s3://biogestor-seed/` y checksums ficticios. No hay contraseñas, tokens ni credenciales.
- **No borra nada:** los registros que no pertenecen a la semilla no se tocan.
- **Versiones inmutables:** `DatasetVersion` y `ModelVersion` se crean y nunca se modifican.

## Datos incluidos

| Entidad | Cantidad | Clave natural | Si ya existe |
| --- | --- | --- | --- |
| Usuarios | 4 | `email` | se actualiza |
| Datasets | 6 (audio, imagen, video, CSV, texto) | `s3_uri` | se actualiza |
| Versiones de dataset | 6 | `(dataset, version_number)` | no se toca |
| Modelos de ML | 3 | `name` | se actualiza |
| Versiones de modelo | 5 | `(model, version_number)` | no se toca |
| Modelo-dataset | 6 | `(model_version, dataset_version)` | no se toca |
| Experimentos | 4 | `(dataset_version, model_version, started_at)` | no se toca |
| Observaciones | 4 | `content` | no se toca |

Relaciones respetadas: cada dataset apunta a un usuario (uno queda sin responsable a propósito, porque `owner` es opcional); cada versión, a su dataset o modelo; cada experimento, a una versión concreta de dataset y de modelo.

## Verificación

Pruebas del comando:

~~~bash
docker compose exec backend python manage.py test apps.datasets.test_seed_data
~~~

Conteo en la base:

~~~bash
docker compose exec backend python manage.py shell -c "from apps.datasets.models import Dataset; from apps.users.models import User; print(User.objects.count(), Dataset.objects.count())"
~~~

Debe imprimir `4 6` en una base vacía. También se puede consultar el catálogo:

~~~bash
curl -i http://127.0.0.1:8080/api/v1/datasets/
~~~

En Windows PowerShell usa `curl.exe` en lugar de `curl`.

## Modelos aún no implementados

Los seeders de versiones, modelos, experimentos y observaciones se escribieron según el modelo de datos preliminar. Si el modelo Django no existe, el seeder se omite con una advertencia; cuando existe, se siembra. **Si los nombres reales son distintos, hay que ajustar `apps/datasets/management/commands/seed_data.py`.**

| Entidad | App | Clases candidatas | Campos usados |
| --- | --- | --- | --- |
| Versión de dataset | `datasets` | `DatasetVersion` | `dataset`, `version_number`, `storage_uri`, `metadata`, `checksum`, `created_by` |
| Modelo | `ml_models` | `MLModel`, `Model` | `name`, `type`, `owner` |
| Versión de modelo | `ml_models` | `ModelVersion` | `model`, `version_number`, `status`, `metrics`, `parameters`, `artifact_uri`, `created_by` |
| Modelo-dataset | `ml_models` | `ModelVersionDatasetVersion`, `ModelVersionDataset` | `model_version`, `dataset_version`, `usage_type` |
| Experimento | `experiments` | `Experiment` | `dataset_version`, `model_version`, `executed_by`, `status`, `metrics`, `started_at`, `finished_at` |
| Observación | `observations` | `Observation`, `Comment` | `kind`, `content`, `author`, `dataset` |

Los nombres de clase se cambian en `MODEL_CANDIDATES`; los campos, en cada función `seed_xxx()`.

## Agregar o ajustar entidades

1. Agregar los datos ficticios en `seed_data.py`.
2. Escribir `seed_xxx()` con una clave natural; debe devolver `(creados, total)`, o `None` si el modelo no existe.
3. Registrarla en `SEEDERS` **después** de las entidades de las que depende.
4. Para versiones usar `get_or_create`, no `update_or_create`.
5. Ejecutar las pruebas: la de idempotencia global cubre también los modelos nuevos de las apps sembradas.




