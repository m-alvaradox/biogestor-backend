# Guía de contribución — BioGestor

## 1. Objetivo

Establecer las convenciones de colaboración para mantener la calidad, organización y trazabilidad del código fuente de BioGestor.

Estas reglas se aplican a los repositorios frontend y backend.

## 2. Estrategia de ramas

La rama `main` contendrá el código estable e integrado.

Cada tarea deberá desarrollarse en una rama independiente creada a partir de la versión más reciente de `main`.

**Convención de nombres:**

- `feature/ID-descripcion`: nuevas funcionalidades.
- `fix/ID-descripcion`: correcciones.
- `docs/ID-descripcion`: documentación.
- `chore/ID-descripcion`: configuración y mantenimiento.

Ejemplo: `feature/S0-07-angular-setup`.

## 3. Commits

Los mensajes de commit deberán describir claramente los cambios realizados.

Se recomienda utilizar los prefijos `feat`, `fix`, `docs`, `refactor`, `test` y `chore`.

Ejemplo: `feat: configurar rutas iniciales de Angular`.

## 4. Pull Requests

Todo cambio destinado a `main` deberá presentarse mediante un Pull Request.

Cada PR deberá:

1. Tener un título descriptivo.
2. Referenciar la tarea de Planner correspondiente.
3. Describir los cambios realizados.
4. Incluir evidencia cuando corresponda.
5. Cumplir las verificaciones técnicas aplicables.
6. Recibir al menos una aprobación de otro integrante, siempre que las protecciones del repositorio lo permitan.

Plantilla Pull Request de ejemplo: https://github.com/m-alvaradox/biogestor-backend/blob/main/.github/pull_request_template.md

No se deben aprobar los propios cambios.

## 5. Revisión de código

El revisor comprobará que los cambios cumplan los criterios de aceptación, respeten las convenciones del proyecto y no introduzcan problemas evidentes.

Las observaciones deberán resolverse antes de integrar el Pull Request.

## 6. Seguridad

Está prohibido subir contraseñas, claves privadas, tokens, credenciales de AWS o archivos `.env` que contengan información sensible.

Se proporcionará un archivo `.env.example` con las variables necesarias y valores de ejemplo no sensibles.

## 7. Documentación

Los cambios que afecten la instalación, configuración, arquitectura o funcionamiento del proyecto deberán acompañarse de la documentación correspondiente.

## 8. Finalización de tareas

Una tarea podrá marcarse como completada en Planner cuando se cumplan sus criterios de aceptación y se adjunte el enlace al entregable correspondiente.

Si implica cambios de código, el Pull Request deberá estar integrado.
