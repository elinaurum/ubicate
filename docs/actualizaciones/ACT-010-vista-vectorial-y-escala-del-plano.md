# ACT-010 — Rediseñar la vista interior como vector y corregir la escala del plano

| Campo | Valor |
|---|---|
| Fecha | 2026-09-15 |
| Versión | 2.0.0 |
| Tipo | funcionalidad / corrección / datos |
| Autor | Claude Code (a pedido de Alexia Roa) |
| Revisado por | |

> Esta nota **corrige y reemplaza parte de**
> [ACT-009](ACT-009-vista-interior-piso-menos1-851.md), que quedó publicada con
> medidas equivocadas. Ambas describen la misma entrega (versión 2.0.0, sin
> desplegar todavía): ACT-009 el diseño inicial, ACT-010 lo que quedó.

## Qué se pidió

Sobre la primera versión de la vista interior, el equipo pidió dos cosas: que
no se viera como un plano de AutoCAD sino como los mapas de los malls
—limpio, fácil de entender—, y que se agregaran los puntos que faltaban
(baños y piscina).

Al preparar ese cambio apareció, además, un error de medida en lo entregado en
ACT-009.

## El error de escala

**Qué pasó.** El DXF declara en su encabezado que está en milímetros
(`$INSUNITS` = 4). Le creí. Está dibujado en **centímetros**. Todo lo que
ACT-009 dejó escrito quedó 10 veces más chico que la realidad:

| Dato | ACT-009 (mal) | Real |
|---|---|---|
| Tamaño del piso | 49,65 × 12,70 m | 101,82 × 71,15 m |
| Sala B01 | — | 9,80 × 4,70 m (46 m²) |
| `coord_interior` de B01–B08 | escala y origen equivocados | recalculadas |

**Cómo se detectó.** Al ir a dibujar las salas como formas, sus medidas daban
1,08 m de ancho: imposible para una sala de clases. Al revisar, ninguna medida
cerraba con la escala declarada.

**Cómo se confirmó**, con cuatro medidas conocidas del propio plano:

| Elemento | unidades | si 1u = 1 mm | si 1u = 1 cm |
|---|---|---|---|
| Ancho típico de puerta (mediana de 294) | 105 | 0,10 m ✗ | **1,05 m ✓** |
| Espesor de muro | 30 | 0,03 m ✗ | **0,30 m ✓** |
| Pilar de hormigón | 80 | 0,08 m ✗ | **0,80 m ✓** |
| Envolvente del edificio | 10210 | 10,21 m ✗ | **102,10 m ✓** |

**Qué se hizo para que no vuelva a pasar:**

- `scripts/extraer_planta_dxf.py` asume centímetros, tiene `--unidad-cm` para
  otros casos, e imprime el ancho típico de puerta como **medida de control**
  en cada corrida, marcándolo "SOSPECHOSO" si sale fuera de 0,7–1,3 m.
- `tests/test_datos.py::test_la_planta_tiene_tamano_de_edificio_real` falla si
  una planta queda con medidas fuera de rango de un edificio real.
- `tests/test_datos.py::test_las_salas_rectangulares_miden_lo_que_una_sala`
  exige que cada sala con contorno tenga entre 20 y 200 m².
- `docs/DATOS.md` §6 advierte del problema y de cómo comprobarlo.

Ningún dato equivocado llegó a producción: la versión 2.0.0 no se ha
desplegado.

## Qué se hizo

**Vista vectorial** (reemplaza la imagen del plano CAD):

- `src/ubicate/mapa/interior.py` — reescrito. Cada sala es una forma con color
  y etiqueta; cada referencia es un símbolo sobre un círculo de color. El piso
  es un fondo gris neutro. Ya no se incrusta la imagen del DXF.
- `assets/plantas/` — eliminado. El HTML pasó de ~170 KB a ~58 KB.
- `modelos.py` — `Sala.poligono_interior` (contorno de la sala);
  `PuntoInteres` y `TipoPunto` (baño, piscina, camarín, ascensor, escalera);
  `PlantaInterior.puntos`; se quitó `PlantaInterior.imagen`.

**Datos del piso -1** (`data/plantas.json`, `data/salas.json`):

- Marco corregido a 101,82 × 71,15 m; `coord_interior` de B01–B08 recalculadas.
- Contorno real para B01, B02, B03, B04 (9,80 × 4,70 m cada una) y B07.
- **24 referencias** nuevas tomadas del rótulo del plano: piscina, 2 camarines,
  7 vestíbulos de baño, 4 halls de ascensor, 8 escaleras.

**Contornos solo si son ciertos:** el script comprueba que la sala sea
rectangular de verdad (compara el área que encierran los muros con la del
rectángulo; exige ≥ 0,97). B05, B06 y B08 no pasan —son hexagonales— y quedan
dibujadas como punto en vez de con una forma inventada.

## Seguridad

Al escribir la prueba de escapado de la vista nueva apareció que **los
tooltips de folium no escapan el contenido**: un rótulo con `<script>` en
`data/` se ejecutaba en el navegador. El popup sí se escapaba desde siempre;
el tooltip no.

Afectaba también a `mapa/render.py`, **el mapa exterior que ya está en
producción**. Se corrigieron ambos (`_tooltip()` en cada módulo) y se agregó
`tests/test_mapa.py::test_tooltip_escapa_contenido_de_los_datos`.

Alcance real: `data/*.json` solo lo edita el equipo, así que no había una vía
de ataque desde fuera. Aun así es la regla 3.4 / §5 de `CLAUDE.md` ("escapa
siempre lo que venga de datos") y estaba incumplida.

## Cómo se probó

- `pytest` (menos `tests/test_proveedores.py`, roto en `main` de antes): 47 ok.
- Pruebas nuevas: escala de la planta, área de las salas, referencias dentro
  del marco, se dibuja polígono, **no** se incrusta imagen CAD, escapado de
  rótulos maliciosos en ambos mapas.
- `ruff check src tests scripts`: limpio.
- `python scripts/validar_datos.py`: 0 errores; avisa qué salas quedaron sin
  contorno.
- Verificación manual: se abrió el HTML de la vista y se revisó que las salas
  caen donde corresponde y que los símbolos de baño/piscina/ascensor/escalera
  están en su lugar.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. Cambia el esquema introducido en esta misma versión (2.0.0), aún sin desplegar |
| ¿Cambia el esquema de `data/`? | Sí: `PlantaInterior.imagen` se va, entran `puntos` y `Sala.poligono_interior` |
| ¿Requiere variables de entorno nuevas? | No |
| ¿Requiere migración? | No |

## Al desplegar

Nada especial. `assets/plantas/` ya no existe: si quedó en algún despliegue
anterior de la rama, se puede borrar.

## Qué quedó pendiente

- **Forma real de B05, B06 y B08** (las salas hexagonales). Hoy son un punto.
- **2 salas del piso -1 sin código oficial confirmado** — `DEUDA_DATOS.md` D-06.
- **Los otros 12 pisos**, con la herramienta ya lista.
- **Sin ruteo** ni entre pisos ni desde el mapa exterior (roadmap §7).
- **El rectángulo gris del fondo es la caja de los muros**, no la silueta real
  del edificio.
- **`tests/test_proveedores.py` sigue roto en `main`** (importa
  `config_pensamiento`, que no existe). Bloquea `make ci` completo y no tiene
  relación con esta entrega.
