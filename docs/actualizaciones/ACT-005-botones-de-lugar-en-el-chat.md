# ACT-005 — Ofrecer los lugares del chat como botones al mapa

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.4.0 |
| Tipo | funcionalidad |
| Autor | Claude Code |
| Revisado por | |

## Qué se pidió

> Cuando se pregunta por un lugar en el chatbot, lo muestra automáticamente en
> el mapa, pero no debería ser así: debería preguntar "¿quieres que te lo
> muestre en el mapa?" y que aparezca como un botón con el lugar en el mismo
> chatbot, que si lo pinchas te lo muestra en el mapa. Esto porque a veces para
> una misma consulta se sugiere más de un lugar.

Decisiones tomadas con el equipo:

- Los botones aparecen solo bajo la **última** respuesta del asistente.
- **Siempre** hay botón, aunque el asistente identifique un solo lugar. El mapa
  nunca se abre sin que el usuario lo pida.

## Qué se hizo

- `src/ubicate/chat/prompts.py` — la sección MAPA pasa de "una sola marca" a
  "una línea `[[LUGAR:ID]]` por cada lugar mencionado, en orden de relevancia,
  máximo cinco". `VERSION_PROMPT` 1.0.0 → 1.1.0.
- `src/ubicate/chat/motor.py` — `Respuesta.destino` → `Respuesta.destinos`
  (tupla). `_extraer_lugar` → `_extraer_lugares`: reúne todas las marcas válidas
  más la coincidencia directa del buscador, sin repetir, tope de cinco.
  `Respuesta.destino` queda como propiedad (el primero) para las métricas.
  `Conversacion.agregar` acepta `citas` y `lugares`.
- `src/ubicate/chat/proveedores.py` — `Mensaje` gana `citas` y `lugares`
  (metadatos de la respuesta; los proveedores solo leen `rol` y `texto`).
- `src/ubicate/modelos.py` — `Destino.etiqueta_corta` ("Sala B04" / nombre del
  edificio) para el texto del botón.
- `src/ubicate/ui/componentes/panel_chat.py` — un botón "📍 …" por lugar de la
  última respuesta; al pulsarlo se fija el destino y se cambia a la vista del
  mapa. Las citas ("de dónde saqué esto") se redibujan desde el historial.
- `src/ubicate/ui/estado.py` — `fijar_destino` ya no cambia la vista a "mapa"
  (se revierte el salto automático de ACT-004); el cambio de vista es explícito
  en el botón.
- `tests/test_motor.py` — pruebas de varias marcas, orden y sin repetir;
  actualizadas las de una marca y marca inválida.
- `pyproject.toml`, `src/ubicate/__init__.py` — versión 1.3.0 → 1.4.0.
- `docs/decisiones/ADR-0007` (supera a ADR-0002); `docs/ARQUITECTURA.md`.

## Por qué así

Detalle en el ADR-0007. Resumen: obligar a un solo lugar descartaba información
("¿en qué sala rindo?" a veces son dos), y el salto automático interrumpía la
lectura de la respuesta y podía llevar al lugar equivocado de los varios
posibles.

## Cómo se probó

- `ruff check` y `pytest` (38 pruebas) en verde con un entorno limpio.
- Prueba manual con `streamlit.testing.v1.AppTest`:
  - Preguntar "B04": la vista **no** cambia; aparece el botón "📍 Sala B04";
    el mensaje guarda `lugares=('B04',)`.
  - Pulsar el botón: cambia a la vista "Mapa" con el destino B04.
  - Varias marcas → varios botones, en orden y sin repetir.
  - Una pregunta de base de conocimiento deja visible "de dónde saqué esto" y
    sus citas quedan guardadas en el mensaje.
  - "Reiniciar conversación" borra mensajes y botones.
- La capa `ui/` no tiene pruebas automatizadas por convención del proyecto.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No para el usuario. En el código, `Respuesta.destino` sigue disponible como propiedad; `Conversacion.agregar` mantiene compatibilidad (los nuevos parámetros son opcionales). |
| ¿Cambia el esquema de `data/`? | No. |
| ¿Requiere variables de entorno nuevas? | No. |
| ¿Requiere migración? | No. |

## Al desplegar

1. Reiniciar el proceso de la aplicación (sube `VERSION_PROMPT`: conviene que
   quede registrado en las métricas del despliegue).

No hay pasos de datos.

## Qué quedó pendiente

- Si el buscador del mapa devuelve varias coincidencias (estado "ambiguo"), el
  chat aún usa solo la marca del modelo. Podría ofrecer también esas
  coincidencias como botones.
- Directorio de personas y unidades como datos estructurados: se abordará en su
  propio ADR (ver `docs/ROADMAP.md`).
