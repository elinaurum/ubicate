# ACT-003 — Diagnosticar fallas del proveedor de modelo

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.2.0 |
| Tipo | funcionalidad + corrección |
| Autor | Equipo U-bícate |
| Revisado por | _pendiente_ |

## Qué se pidió

El chat respondía "tuve un problema para responder" ante toda consulta, sin
ninguna pista de la causa. El mapa y la búsqueda funcionaban bien.

## Qué se hizo

- `scripts/probar_proveedor.py` — diagnóstico de la conexión con el proveedor.
  Muestra la configuración activa, hace una llamada real, y traduce el error del
  servicio a una causa concreta con su solución (modelo inexistente, key
  inválida, cuota agotada, sin red, sin permisos). Ante un fallo lista además los
  modelos que la key sí tiene disponibles.
- `src/ubicate/ui/componentes/panel_chat.py` — fuera de producción, la interfaz
  muestra el detalle técnico del error bajo la respuesta. Antes la causa quedaba
  solo en el log de la terminal, donde se perdía.
- `src/ubicate/chat/proveedores.py` — `con_reintento`: hasta tres intentos con
  espera creciente **solo** ante errores de límite de velocidad (429). No
  reintenta ante otros errores, porque un modelo inexistente no se arregla
  esperando. Resuelve el pendiente declarado en ACT-002.
- `CLAUDE.md` — instrucciones permanentes para trabajar con Claude Code en el
  repositorio.
- `Makefile` — objetivo `make probar`.
- `tests/test_proveedores.py` — dos pruebas del reintento.

## Por qué así

El error genérico era correcto de cara al estudiante: no tiene por qué ver un
mensaje del proveedor. El problema es que el equipo tampoco lo veía. La solución
es mostrar el detalle solo cuando `UBICATE_ENTORNO` no es `produccion`, que ya
era el valor por defecto en desarrollo.

El reintento se limitó a los errores 429 a propósito. Reintentar ante cualquier
fallo triplica la latencia de un error que igual va a ocurrir, y en las capas
gratuitas gasta cuota sin necesidad.

## Cómo se probó

- 37 pruebas en verde (2 nuevas), `ruff` sin observaciones, `make validar` limpio.
- El script verificado en tres escenarios: modo eco, key sin la librería
  instalada, y configuración incompleta.

> Pendiente: verificar el script contra un fallo real de red con una key válida.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

Confirmar que `UBICATE_ENTORNO=produccion` en el `.env` de producción, para que
el detalle técnico no le llegue al estudiante.

## Qué quedó pendiente

- Reintento con respeto de la cabecera `Retry-After` cuando el proveedor la envía.
- Aviso en la interfaz cuando el proveedor está degradado de forma sostenida, en
  vez de un error por consulta.
