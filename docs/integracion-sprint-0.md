# Integración Sprint 0

## Preparación

Con PostgreSQL y backend activos:

docker compose exec backend python manage.py migrate

Crear o actualizar el registro sintético desde la consola Django:

docker compose exec backend python manage.py shell

from apps.core.models import IntegrationProbe
IntegrationProbe.objects.update_or_create(
    id="sprint-0",
    defaults={"message": "BioGestor: prueba de integración Sprint 0"},
)

## Endpoint

GET http://localhost:8080/api/v1/integration/

Solo está habilitado con DEBUG=True y permite consultar datos sintéticos
sin autenticación.

- 200: devuelve id y message del registro sprint-0.
- 404: registro ausente o sonda deshabilitada con DEBUG=False.
- 405: método de escritura no permitido.

## Verificación

docker compose exec backend python -m coverage run manage.py test apps.core
docker compose exec backend python -m coverage report --fail-under=70

Resultado local: seis pruebas correctas y 100 % de cobertura en
apps/core/views.py y apps/core/models.py.

El flujo manual con Angular verificó consulta, actualización del mensaje,
registro ausente y recuperación sin recargar la página.