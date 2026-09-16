# ACT-011 — Modelar el piso -1 completo, recinto por recinto

| Campo | Valor |
|---|---|
| Fecha | 2026-09-15 |
| Versión | 2.0.0 |
| Tipo | funcionalidad |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

> Tercera y última iteración de la vista interior dentro de la versión 2.0.0,
> que aún no se despliega. Las anteriores:
> [ACT-009](ACT-009-vista-interior-piso-menos1-851.md) (imagen del plano CAD) y
> [ACT-010](ACT-010-vista-vectorial-y-escala-del-plano.md) (vector + corrección
> de escala). Decisión: [ADR-0009](../decisiones/ADR-0009-vista-interior-de-piso.md).

## Qué se pidió

Sobre la versión anterior, el equipo corrigió el rumbo: no quería las salas
"como figuras flotando en un espacio blanco" sino **todo el piso modelado**,
con las estructuras siguiendo la forma que tienen en el plano; cada una puede
ser simple —una figura con borde y fondo—; todo gris; y que un destino se
ponga **verde cuando el cursor está encima**, como retroalimentación.

## El problema de fondo

El plano de arquitectura **no trae las salas como figuras cerradas**: solo los
trazos de sus muros. No hay ningún polígono "sala" que copiar. Las dos salidas
fáciles eran malas: dibujar los muros como líneas (se lee como plano técnico,
y una línea no puede responder al cursor) o inventarle un rectángulo a cada
sala (rompe la regla 3.1, y las salas hexagonales del piso quedarían mal).

## Qué se hizo

**Reconstrucción de los recintos** (`scripts/extraer_planta_dxf.py --recintos`):
se dibujan muros, tabiques, puertas y ascensores sobre una grilla de 5 cm, se
buscan las bolsas de espacio que quedan cerradas entre ellos, y se traza y
simplifica el contorno de cada una. Del piso -1 salieron **287 recintos** que
cubren 4.481 m² (el umbral de área mínima se bajó a 1,5 m² para que aparezcan
los baños y otros espacios chicos). Todo sale del trazado del plano; no se dibuja nada a mano.

- `assets/plantas/851_SUBTE1.geojson` — 263 recintos comunes (pasillos, halls,
  servicios, salas de máquinas).
- `data/salas.json` — los recintos que son salas del catálogo pasaron a
  `poligono_interior`. **Ahora las 9 tienen su forma real**, incluidas las
  hexagonales que en ACT-010 quedaron como punto.
- `data/plantas.json` — campo `geometria` apuntando al GeoJSON, y `poligono`
  en cada referencia que tiene recinto propio.
- `src/ubicate/mapa/interior.py` — reescrito: dibuja el piso completo con
  `folium.GeoJson`; los recintos comunes en gris y sin interacción; las salas y
  las referencias con `highlight_function`, que es el resaltado en verde bajo
  el cursor.
- `src/ubicate/modelos.py` — `PlantaInterior.geometria`, `PuntoInteres.poligono`.
- `src/ubicate/config.py` — `dir_plantas`.
- `scripts/validar_datos.py` — informa cuántos recintos trae cada planta y
  falla si falta el archivo de geometría.

**Referencias como figuras** (segunda ronda, a pedido del equipo): baños,
camarines y piscina también se dibujan como figura rellena, no solo como
símbolo. **15 de 24** lo consiguen: todos los baños, los 2 camarines, la
piscina y 3 escaleras. Los 4 halls de ascensor y 5 escaleras siguen como
símbolo, porque el plano no los encierra como recinto propio: un hall de
ascensores está dentro de la circulación general, y una escalera está trazada
con sus peldaños, que la fragmentan. Se prefirió eso a asignarles el recinto
más cercano, que en las pruebas apuntaba a cuartos ajenos a 3 m de distancia.

**La piscina, caso aparte.** La reconstrucción por grilla le daba 36,9 m²: una
franja de 3,30 m, porque los andariveles dibujados dentro la cortan. Su forma
real está en el plano como un rectángulo cerrado de cuatro muros:
**25,00 × 12,50 m** (312,5 m², medida de piscina de competición). Para
obtenerla se agregó `--rectangulo` al script, que busca el rectángulo cerrado
de muros más chico que contiene un punto, ignorando lo dibujado dentro.

**B09 agregada.** En la ronda anterior no se cargó por prudencia, junto con
B10. Era un exceso: el equipo había dado B09 = "SALA DE CLASES 05" de forma
directa, y solo B10 como intuición. B09 ya está en `data/salas.json`, con su
contorno (29,6 m²) y con `edificio_id: 851_INGMEC`, departamento que el equipo
confirmó aparte — el plano no nombra departamentos, así que no era deducible.

**Paleta:** todo el piso en grises. El verde (`#1E8449` borde, `#A9DFBF`
relleno) se usa **solo** para "el cursor está sobre este destino".

## Seguridad

Otro escapado faltante, del mismo tipo que el de ACT-010 pero por otra vía:
`folium.GeoJsonTooltip` termina insertando el valor con `innerHTML`, así que un
rótulo del plano con `<img src=x onerror=…>` se ejecutaría. Lo encontró la
prueba de escapado al migrar a GeoJSON. Se escapa al construir las *features*
(`_feature_sala`, `_feature_punto`) y hay prueba de regresión.

## Cómo se probó

- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 51 ok.
- Pruebas nuevas: el piso se dibuja completo (más de 100 recintos), las 9 salas
  tienen contorno, las referencias con recinto se dibujan como figura, el verde
  del cursor está presente, no se incrusta imagen CAD, y el escapado con
  `<img onerror=…>`.
- `ruff check src tests scripts`: limpio.
- `python scripts/validar_datos.py`: 0 errores, 0 avisos.
- Verificación manual: se rindió el piso completo a imagen y se revisó que la
  planta es coherente —la piscina, los halls, la fila de 4 salas de clases y
  los auditorios aparecen donde corresponde y con su forma.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. Cambia el esquema introducido en esta misma versión (2.0.0), aún sin desplegar |
| ¿Cambia el esquema de `data/`? | Sí: `PlantaInterior.geometria`, `PuntoInteres.poligono`; `poligono_interior` en las 9 salas |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

`assets/plantas/851_SUBTE1.geojson` tiene que viajar con el repositorio, igual
que `assets/mapa_beauchef.png`. Sin él la vista interior sale vacía (y
`make validar` lo avisa).

## Qué quedó pendiente

- **El recinto de ~850 m²** es todo el sistema de circulación junto: los
  pasillos abiertos entre sí se funden en una figura. Separarlos exige cortar
  a mano por los umbrales.
- **Nombrar los recintos comunes.** Hoy son figuras grises sin etiqueta; el
  plano tiene el rótulo de muchos ("SALA TALLER", "BODEGA", "CLIMATIZACION") y
  se podrían cruzar por posición, igual que se hizo con las salas.
- **Ascensores y 5 escaleras siguen como símbolo**, no como figura: el plano no
  les da recinto propio. Darles forma exige decidir a mano qué superficie
  ocupan.
- **1 sala del piso -1 sin código oficial confirmado** ("SALA DE CLASES 09") —
  `DEUDA_DATOS.md` D-06.
- **Los otros 12 pisos**, con la herramienta ya lista.
- **Sin ruteo** ni entre pisos ni desde el mapa exterior (roadmap §7).
- **`tests/test_proveedores.py` sigue roto en `main`**; bloquea `make ci`
  completo y no tiene relación con esta entrega.
