# ACT-004 — Reorganizar la interfaz para uso en el teléfono

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.3.0 |
| Tipo | funcionalidad |
| Autor | Claude Code |
| Revisado por | |

## Qué se pidió

> Quiero cambiar la interfaz de la aplicación. Hoy el chatbot y el mapa conviven
> en la misma ventana y siento que eso no funcionaría bien en un celular. La idea
> es que la aplicación se use en un celular, así que reorganiza cómo se verá.

## Qué se hizo

- `src/ubicate/ui/app.py` — `layout="wide"` → `layout="centered"` y la barra
  lateral arranca cerrada. Se reemplazan las dos columnas (chat | mapa) por un
  selector `st.segmented_control` "💬 Preguntar" / "🗺️ Mapa" que muestra un
  panel a la vez, a pantalla completa. El selector refleja la vista guardada en
  el estado (se copia al widget antes de crearlo).
- `src/ubicate/ui/estado.py` — nueva clave de sesión `VISTA` (`chat` / `mapa`)
  con `vista()` y `fijar_vista()`. `fijar_destino()` ahora cambia la vista a
  `mapa` cuando el destino no es nulo: el puente chat → mapa lleva al usuario al
  plano en vez de actualizarlo fuera de su vista.
- `src/ubicate/ui/componentes/barra_lateral.py` — se quita el selector
  "¿Dónde estás ahora?". Queda: reiniciar conversación, versión y diagnóstico,
  avisos de contenido vencido y conflictos.
- `src/ubicate/ui/componentes/panel_mapa.py` — el selector de punto de partida
  se muestra aquí, junto al buscador, dentro de un desplegable que lleva en la
  etiqueta la partida elegida.
- `pyproject.toml`, `src/ubicate/__init__.py` — versión 1.2.0 → 1.3.0. Piso de
  `streamlit` 1.36 → 1.50 (`st.segmented_control`).
- `docs/ARQUITECTURA.md` — se actualiza la descripción de la interfaz.
- `docs/decisiones/ADR-0006` — la decisión de navegación y por qué no pestañas.

## Por qué así

Alternativas en el ADR-0006. Resumen: las pestañas (`st.tabs`) no se pueden
cambiar desde el servidor, así que el chat no podría llevar al usuario al mapa;
un layout que se adapte al ancho del navegador exige un componente extra para
medirlo, y el público usa la herramienta casi siempre desde el teléfono.

## Cómo se probó

- `ruff check` y `pytest` (37 pruebas) en verde con un entorno limpio.
- Prueba manual con `streamlit.testing.v1.AppTest`:
  - Al abrir: vista "Preguntar", subtítulo "Pregúntame".
  - Con un destino fijado: la vista salta a "Mapa", aparece "Mapa del campus" y
    el selector de punto de partida.
  - Volver a "Preguntar" restaura el chat. Sin excepciones en ningún paso.
- Verificación manual pendiente en un teléfono real (ver "Qué quedó pendiente").
- La capa `ui/` no tiene pruebas automatizadas por convención del proyecto
  (importa Streamlit; ver `docs/ARQUITECTURA.md`).

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. Mismo dominio, mismas funciones; cambia solo la disposición visual. |
| ¿Cambia el esquema de `data/`? | No. |
| ¿Requiere variables de entorno nuevas? | No. |
| ¿Requiere migración? | No. |

## Al desplegar

1. Reinstalar dependencias para tomar el nuevo piso de Streamlit:
   `pip install -r requirements-dev.txt` (o `pip install -e .`).
2. Reiniciar el proceso de la aplicación.

No hay pasos de datos.

## Qué quedó pendiente

- Probar en un teléfono real: altura del plano (`UBICATE_MAPA_ALTO_PX`, hoy 620)
  y del historial del chat (`st.container(height=420)` en `panel_chat.py`), que
  se fijaron para el layout de dos columnas y quizá convenga subir ahora que
  cada panel ocupa toda la pantalla.
- PWA con manifiesto e íconos (`docs/ROADMAP.md` §5), para que se instale como
  aplicación. Es el paso siguiente natural y no se abordó aquí.
- `tests/test_proveedores.py::test_eco_es_el_valor_por_defecto` falla si hay un
  `.env` con `UBICATE_PROVEEDOR_LLM` en la máquina: la prueba no aísla el
  entorno. Es previo a este cambio y no lo toca; anotarlo para corregirlo aparte.
