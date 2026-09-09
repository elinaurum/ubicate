# ACT-007 — Mejorar la calidad de las respuestas del chat

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.4.2 |
| Tipo | corrección |
| Autor | Claude Code |
| Revisado por | |

## Qué se pidió

> Hay que mejorar la calidad de las respuestas del chatbot. Pregunté "dónde
> puedo ir a estudiar" y respondió con una frase cortada ("Biblioteca de 850 y
> la") y citó como fuente "Dónde puedo conseguir paletas de ping pong".

## Diagnóstico

1. **Fuente irrelevante.** La consulta se reduce a las palabras `puedo` +
   `estudiar`. `puedo` aparece en el título de muchos fragmentos redactados como
   pregunta ("¿Dónde puedo conseguir…?"), así que ese fragmento puntúa casi
   igual (7.20) que el correcto (7.24). Las palabras vacías de `busqueda/`
   están pensadas para "sala B04", no para preguntas en prosa.
2. **Respuesta cortada.** No es el límite de tokens (700). Es el filtro de
   "recitación" de Gemini: corta la generación cuando el modelo copia el
   contexto casi textual. `ProveedorOpenAI` no miraba `finish_reason` y devolvía
   el fragmento truncado sin avisar.

## Qué se hizo

- `src/ubicate/chat/conocimiento.py` — nueva lista `VACIAS_TEXTO` (palabras de
  pregunta y muletillas: "puedo", "hay", "cómo", "cuál", "campus"…) y
  `tokens_texto()`, que se usa al indexar y al consultar. "dónde puedo ir a
  estudiar" ahora recupera solo "Espacios para estudiar".
- `src/ubicate/chat/proveedores.py` — `ProveedorOpenAI.responder` revisa
  `finish_reason`: lo registra si no es "stop", y lanza `ErrorProveedor` si la
  respuesta viene vacía o bloqueada por filtro/recitación, en vez de devolver
  texto a medias. El motor ya degrada con gracia ante `ErrorProveedor`.
- `src/ubicate/chat/prompts.py` — la regla de FUNDAMENTACIÓN ahora pide
  **reformular con palabras propias y no copiar frases del contexto**. Mejora el
  estilo y evita el corte por recitación de Gemini. `VERSION_PROMPT` 1.1.0 →
  1.2.0.
- `docs/DATOS.md` §5 — guía para el equipo de contenidos: el título del fragmento
  lleva las palabras del tema, no las de la pregunta.
- `tests/test_conocimiento.py`, `tests/test_proveedores.py` — pruebas de la
  precisión de recuperación y del manejo de `finish_reason`.
- `pyproject.toml`, `src/ubicate/__init__.py` — versión 1.4.1 → 1.4.2.

## Por qué así

El cambio de recuperación vive dentro de `BaseConocimiento`, que es justo lo que
ADR-0003 dice que se puede tocar sin que el resto se entere. No se cambia a
embeddings: el problema era ruido léxico de palabras de pregunta, no falta de
comprensión semántica; la lista de palabras vacías lo resuelve sin dependencias.

## Cómo se probó

- `ruff check` y `pytest` (43 pruebas) en verde con un entorno limpio.
- Diagnóstico manual sobre 7 consultas típicas ("dónde estudio", "dónde
  almuerzo", "quién es el decano", "cómo pido una franquicia", "dónde hay
  microondas"…): en todas mejora o se mantiene la precisión; ninguna empeora.
- `python scripts/validar_datos.py` sin errores.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. Cambia el ranking de recuperación (a mejor) y el prompt. |
| ¿Cambia el esquema de `data/`? | No. |
| ¿Requiere variables de entorno nuevas? | No. |
| ¿Requiere migración? | No. Al reindexar en el próximo arranque, los fragmentos toman los nuevos tokens. |

## Al desplegar

1. Reiniciar el proceso (sube `VERSION_PROMPT`; conviene que quede en las
   métricas del despliegue).

## Qué quedó pendiente

- **Lugares del catálogo.** "pajarera", "CEC", "Taller de los Dos Relojes" y las
  salas de estudio por departamento se mencionan en la base pero no están en el
  índice espacial, así que el chat solo puede ofrecer el botón de la Biblioteca.
  Es la deuda D-03 / ROADMAP §2.
- **Sin raíces ni sinónimos.** "dónde almuerzo" no recupera "Espacios para
  almorzar" ("almuerzo" ≠ "almorzar"). Sigue siendo la limitación conocida de
  ADR-0003; se mitiga con los títulos.
- Revisar el registro de consultas sin respuesta tras unas semanas de uso real,
  como dice ADR-0003, para decidir si hace falta algo más.
