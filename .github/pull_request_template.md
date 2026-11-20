## Descripción

Describe el objetivo, los cambios realizados y su justificación.

## Tarea e Issues relacionados

- Planner: S1-XX, PB-XX
- Issue: Closes #n
- PR de frontend (si aplica):

## Tipo de cambio

- [ ] Nueva funcionalidad
- [ ] Corrección de bug
- [ ] Refactorización
- [ ] Documentación / configuración
- [ ] Base de datos / migraciones

## Cómo probarlo

**Precondiciones:**
**Pasos para verificar el cambio:** 1. 2. 3.

**Resultado esperado:**

## Evidencia (obligatoria según tipo de cambio)

Adjuntar según corresponda:
- CI en verde y cobertura >= 70 %.
- Request/response de API (éxito y error).
- Migraciones verificadas en PostgreSQL limpio.
- Pruebas de permisos por rol.
- Integración con frontend.

No incluir información sensible.

Las capturas adjuntadas deben tener este tipo de formato en el nombre para una mejor trazabilidad IDtarea_descripcion_AAAAMMDD.

## Definition of Done

- [ ] Cumple los criterios de aceptación.
- [ ] Ruff lint y formato sin errores.
- [ ] Pruebas unitarias agregadas o actualizadas.
- [ ] Cobertura >= 70 % y CI en verde.
- [ ] Migraciones incluidas y verificadas (si aplica).
- [ ] Endpoints documentados (si aplica).
- [ ] Permisos y validaciones verificados.
- [ ] Sin credenciales ni datos sensibles.
- [ ] Variables nuevas en .env.example.
- [ ] Integración con frontend verificada (si aplica).
- [ ] Evidencia de pruebas adjunta.
- [ ] Documentación actualizada (si aplica).

## Observaciones

Dependencias, limitaciones o excepciones.
Justificar si el PR supera 400 líneas