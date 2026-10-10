# Guía de contribución — BioGestor

## 1. Objetivo

Establecer las convenciones de colaboración para mantener la calidad, organización y trazabilidad del código fuente de BioGestor. Estas reglas se aplican a los repositorios frontend y backend y siguen la Guía de Calidad del proyecto.

## 2. Estrategia de ramas

- **main**: código de producción. Está protegida y recibe cambios desde develop al cerrar el sprint, o desde una rama hotfix/*.
- **develop**: rama de integración del sprint. Recibe Pull Requests de feature/*, fix/* y chore/*.
- **feature/<ID>-descripcion**: nueva funcionalidad o tarea técnica. Se crea desde develop y se integra a develop por Pull Request.
- **fix/<número-Issue>-descripcion**: corrección de un error del sprint. Se crea desde develop y se integra a develop por Pull Request.
- **chore/<ID>-descripcion**: configuración, mantenimiento o infraestructura. Se crea desde develop y se integra a develop por Pull Request.
- **hotfix/<número-Issue>-descripcion**: corrección urgente de producción. Se crea desde main; después de integrarse a main, el cambio se sincroniza con develop.

No se deben hacer push directos ni force push a main o develop.

## 3. Commits

Los mensajes de commit deben describir claramente los cambios. Se recomiendan los prefijos feat, fix, docs, refactor, test y chore.

Ejemplo: chore: inicializar estructura modular de Django.

## 4. Pull Requests

Todo cambio destinado a develop o main se presenta mediante un Pull Request. Cada PR debe:

1. Tener un título descriptivo.
2. Referenciar la tarea de Planner correspondiente y el Issue de GitHub cuando exista.
3. Describir los cambios realizados y por qué se necesitan.
4. Explicar cómo probarlos e incluir evidencia cuando corresponda.
5. Cumplir las verificaciones técnicas aplicables.
6. Recibir al menos una aprobación de otro integrante y la aprobación del CODEOWNER del área, según la Guía de Calidad.
7. No ser aprobado por su propio autor.

Plantilla de Pull Request: .github/pull_request_template.md.

## 5. Revisión de código

El revisor comprobará los criterios de aceptación, pruebas, legibilidad, seguridad, manejo de errores y consistencia arquitectónica. Las observaciones bloqueantes deben resolverse antes del merge.

## 6. Seguridad

Está prohibido subir contraseñas, claves privadas, tokens, credenciales de AWS o archivos .env con información sensible. Las variables necesarias deben documentarse en .env.example con valores de ejemplo no sensibles. El archivo .env debe permanecer ignorado por Git.

## 7. Documentación y pruebas

Los cambios que afecten la instalación, configuración, arquitectura o funcionamiento se acompañarán de documentación. Los endpoints nuevos tendrán pruebas automatizadas; la cobertura mínima exigida por la Guía de Calidad es del 70 % cuando exista infraestructura de pruebas.

## 8. Finalización de tareas

Una tarea puede marcarse como completada en Planner cuando cumpla sus criterios de aceptación, el Pull Request esté aprobado e integrado en develop y la evidencia correspondiente esté enlazada. El paso de develop a main ocurre durante el release después de la Sprint Review y la aceptación del Product Owner.
