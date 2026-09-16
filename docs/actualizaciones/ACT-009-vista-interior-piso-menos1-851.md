# ACT-009 — Agregar la vista interior del piso -1 (851)

| Campo | Valor |
|---|---|
| Fecha | 2026-09-15 |
| Versión | 2.0.0 |
| Tipo | funcionalidad / datos |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

## Qué se pidió

El equipo consiguió los planos de arquitectura (DWG) de los 13 pisos del
edificio 851 y pidió construir con ellos un mapa interior, empezando por el
piso -1 (donde están las salas B01–B08). Pidieron explícitamente que fuera
**una vista aparte**, sin mezclarla con el mapa exterior actual.

## Qué se hizo

- `src/ubicate/modelos.py` — nuevo modelo `PlantaInterior`; nuevo campo
  opcional `Sala.coord_interior` (metros, sistema propio del piso).
- `data/plantas.json` — nuevo archivo. Una entrada: `851_SUBTE1` (piso -1),
  con el tamaño real del plano (49,65 × 12,70 m).
- `data/salas.json` — `coord_interior` agregado a `B01`–`B08`, con la posición
  real extraída del plano de arquitectura.
- `assets/plantas/851_piso_-1.png` — imagen del piso, generada desde el DXF
  (muros, tabiques, puertas, ascensores y texto).
- `src/ubicate/mapa/interior.py` — nuevo módulo, mismo patrón que
  `mapa/render.py` (ADR-0004): folium con `crs="Simple"`, HTML autocontenido,
  sin importar Streamlit.
- `src/ubicate/datos/repositorio.py` — carga y valida `plantas.json`;
  `planta_de()` y `salas_en_planta()`; valida que toda `coord_interior` caiga
  dentro de su planta.
- `src/ubicate/config.py` — `ruta_plantas`, `dir_imagenes_plantas`.
- `src/ubicate/ui/recursos.py` y `ui/componentes/panel_mapa.py` — la ficha del
  destino ofrece un desplegable "Ver el interior del piso" cuando existe.
- `scripts/extraer_planta_dxf.py` — herramienta nueva para convertir un DXF de
  arquitectura en la imagen + coordenadas que este esquema necesita. Se corre
  a mano, una vez por piso; no es parte de la aplicación (`ezdxf` y
  `matplotlib` quedan como dependencia opcional `pip install .[planos]`).
- `docs/DATOS.md` §6 — esquema de `plantas.json` y procedimiento para agregar
  un piso nuevo.
- `docs/DEUDA_DATOS.md` D-06 — resuelta para `B01`–`B08`; sigue abierta para 2
  salas del piso sin código oficial confirmado.
- `docs/decisiones/ADR-0009-vista-interior-de-piso.md` — nuevo.

## Por qué así

Ver ADR-0009. En resumen: vista aparte (no una capa del mapa exterior) porque
calzarlas exige georreferenciar, que no hace falta todavía; coordenadas en el
sistema propio de cada piso porque son las que da el plano de verdad, sin
inventar una conversión.

La correspondencia entre "SALA DE CLASES NN" del plano y el código oficial
`B0X` la confirmó el equipo en terreno — no se dedujo (regla 3.1). Dos salas
del piso quedaron sin cargar porque esa confirmación no llegó completa.

## Cómo se probó

- `tests/test_datos.py` — 4 pruebas nuevas: toda `coord_interior` cae dentro
  de su planta, un edificio no tiene planta, una sala sin plano da `None` sin
  reventar, y las 8 salas B aparecen en `salas_en_planta`.
- `tests/test_mapa_interior.py` — nuevo archivo: el HTML incluye el plano
  embebido, dibuja las salas, y no revienta con una planta sin salas.
- `python scripts/validar_datos.py` — 0 errores, 0 avisos; confirma que la
  imagen de la planta existe.
- `pytest` completo (excepto `tests/test_proveedores.py`, que ya estaba roto
  en `main` antes de este cambio — ver "Qué quedó pendiente"): 44 pruebas, ok.
- `ruff check src tests scripts`: sin errores.
- Verificación manual: se generó la imagen y se revisó visualmente que cada
  código `B0X` cae dentro de su sala real en el plano (no en un lugar
  arbitrario), superpuesto con marcadores de prueba antes de escribir los
  datos definitivos.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. `coord_interior` es opcional; sin `plantas.json` la app funcionaba igual, pero ahora el archivo existe siempre (lista vacía si no hay pisos) |
| ¿Cambia el esquema de `data/`? | Sí: archivo nuevo (`plantas.json`) y campo nuevo en `salas.json`. Por eso versión **MAYOR** |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No — datos existentes siguen válidos sin `coord_interior` |

## Al desplegar

Ninguno especial: los archivos nuevos (`data/plantas.json`,
`assets/plantas/851_piso_-1.png`) se despliegan junto con el resto del
repositorio, igual que `assets/mapa_beauchef.png`.

## Qué quedó pendiente

- **2 salas del piso -1 sin código oficial confirmado** ("SALA DE CLASES 05" y
  "09" del plano) — `docs/DEUDA_DATOS.md` D-06.
- **Si los hexágonos del plano son una sala o dos** — cada uno de los 3
  "hexágonos" del piso trae dos rótulos de sala muy próximos; falta confirmar
  si hay un tabique real entre ellos.
- **Los otros 12 pisos del 851** quedan con la misma herramienta lista
  (`scripts/extraer_planta_dxf.py`) pero sin procesar.
- **Sin ruteo entre pisos ni desde el mapa exterior** — esta entrega es solo
  la vista; el roadmap §7 sigue teniendo pendientes el grafo de navegación y
  el motor de rutas (con la variante accesible sin escaleras, que no es
  opcional).
- **`tests/test_proveedores.py` está roto en `main`**, de antes de este
  cambio: importa `config_pensamiento`, que no existe en
  `ubicate/chat/proveedores.py`. No se tocó porque es un problema aparte, sin
  relación con esta entrega — pero bloquea que `pytest` corra completo y por
  lo tanto bloquea `make ci` tal como está hoy. Conviene arreglarlo pronto.
