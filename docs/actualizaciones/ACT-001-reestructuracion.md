# ACT-001 — Reestructurar el proyecto sobre una arquitectura mantenible

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.0.0 |
| Tipo | infraestructura + corrección + documentación |
| Autor | Equipo U-bícate |
| Revisado por | _pendiente_ |

## Qué se pidió

Tomar el prototipo, que estaba hecho de forma rudimentaria, y dejarlo ordenado y
documentado para poder implementarlo en la facultad con al menos 2.000 usuarios.

## Qué se hizo

### Estructura

- `src/ubicate/` — el `app.py` de 340 líneas se separó en capas: `modelos.py`,
  `config.py`, `busqueda/`, `datos/`, `mapa/`, `chat/`, `observabilidad/`, `ui/`.
- `app.py` en la raíz queda solo como lanzador de `streamlit run app.py`.
- `pyproject.toml`, `requirements.txt`, `Makefile`, `Dockerfile`,
  `.streamlit/config.toml`, `.env.example`, `.gitignore`.
- `.github/workflows/ci.yml` — linter, pruebas y validación de datos en cada PR.

### Datos

- `scripts/migrar_datos_v0_v1.py` — migración reproducible al esquema nuevo, en
  vez de edición manual. Agrega `acceso` y `tipo`, convierte `piso` a entero,
  poda alias redundantes, repara los corruptos y fusiona el duplicado Gorbea.
- `scripts/importar_kb.py` — parte el documento maestro en `data/kb/` con
  cabecera de metadatos: fuente, fecha de actualización y vigencia.
- `scripts/validar_datos.py` — validación con código de salida, para CI.

### Funcionalidad

- Búsqueda tolerante a formato, con desambiguación y sugerencias por similitud.
- Puente automático chat → mapa mediante la marca `[[LUGAR:ID]]` (Objetivo 3).
- Selección manual del punto de partida.
- Modo eco: la aplicación funciona sin API key ni modelo de lenguaje.
- Límites de mensajes por sesión y de frecuencia.
- Registro de consultas, incluidas las que quedan sin responder.

### Correcciones

Ver la sección "Corregido" del [CHANGELOG](../../CHANGELOG.md#100--2026-09-08).
Las de fondo: el plano no se veía, los datos se insertaban sin escapar en el
HTML, la búsqueda distinguía mayúsculas y guiones, y había alias ambiguos que
resolvían en silencio al lugar equivocado.

## Por qué así

Las cuatro decisiones estructurales quedaron en ADR, porque van a condicionar lo
que venga:

- [ADR-0001](../decisiones/ADR-0001-arquitectura-por-capas.md) — capas con el
  dominio separado de Streamlit.
- [ADR-0002](../decisiones/ADR-0002-marca-de-lugar-para-el-mapa.md) — contrato
  `[[LUGAR:ID]]` en vez de detección de nombres o tool use.
- [ADR-0003](../decisiones/ADR-0003-bm25-en-vez-de-embeddings.md) — BM25 en
  Python puro.
- [ADR-0004](../decisiones/ADR-0004-mapa-como-html-cacheado.md) — mapa como HTML
  cacheado, sin `streamlit-folium`.

Sobre lo que **no** se hizo: las inconsistencias de datos que requieren
verificación en terreno se dejaron anotadas en
[DEUDA_DATOS.md](../DEUDA_DATOS.md) en vez de corregirse a ojo. Un dato inventado
con seguridad es peor que un dato ausente, y esa es justamente la propiedad que
sostiene la credibilidad del asistente.

## Cómo se probó

- 30 pruebas automatizadas: normalización, búsqueda, integridad de los datos
  reales, recuperación de conocimiento, motor de chat y renderizado del mapa.
- `ruff check` sin observaciones.
- `python scripts/validar_datos.py` — 0 errores, 0 avisos.
- Arranque de la aplicación verificado, sin errores en el log.
- Verificación manual: búsqueda de `B04`, `b-04`, `sala B 04`, `física`,
  `auditorio` (desambigua), `biblioteka` (sugiere), `zzzqqq` (avisa).

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | Sí. El `app.py` anterior queda reemplazado |
| ¿Cambia el esquema de `data/`? | Sí. Campos nuevos `acceso` y `tipo`; `piso` pasa a entero |
| ¿Requiere variables de entorno nuevas? | Opcionales, todas con valor por defecto. Sin `.env` la app funciona en modo eco |
| ¿Requiere migración? | Sí, ya ejecutada. `make migrar` la reproduce |

## Al desplegar

1. `pip install -r requirements.txt` (cambian las dependencias:
   sale `streamlit-folium`, entran `pydantic` y `pydantic-settings`).
2. Copiar `.env.example` a `.env` y completar el proveedor de modelo si se va a usar.
3. `make validar` antes de levantar.
4. Prueba de humo: buscar `B04` y preguntar "dónde almuerzo".

## Qué quedó pendiente

- Completar la tabla de responsables de contenidos en
  [OPERACION.md](../OPERACION.md) §1. Es lo que decide si el proyecto sobrevive
  al cambio de semestre.
- Verificar en terreno las deudas D-01 y D-02.
- Fijar versiones (`requirements.lock`) antes de la primera puesta en producción.
- Todo lo de [ROADMAP.md](../ROADMAP.md).
