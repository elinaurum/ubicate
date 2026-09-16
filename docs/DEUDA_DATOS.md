# Deuda de datos

Inconsistencias detectadas en los datos heredados del prototipo que **no se
corrigieron** porque requieren verificación en terreno. Corregirlas inventando
sería peor que dejarlas anotadas: un dato inventado con seguridad hace más daño
que un dato ausente.

Al resolver cada una: corregir el archivo, marcar aquí como resuelta con fecha, y
dejar la nota de actualización.

---

## D-01 · Salas `Q*` asignadas al edificio de Minas

**Estado:** abierta · **Impacto:** alto — el marcador puede caer en el edificio
equivocado.

Las salas `QP`, `QO`, `Q10`, `Q21`, `Q22`, `Q23` tienen `edificio_id:
"850_MINAS"` (Ingeniería de Minas), pero sus propias instrucciones dicen "entra
al edificio de Química". No existe un edificio de Química en el sector 850 dentro
de `edificios.json`; el único registro de Química es `851_INGQUIM`, en el otro
sector.

**Qué hay que hacer:** ir al campus y confirmar dónde están físicamente las salas
Q. Si están en un edificio no registrado, agregarlo con su coordenada. Si están
efectivamente en Minas, corregir el texto de las instrucciones.

---

## D-02 · Salas `E213`–`E216` marcadas en piso 1

**Estado:** abierta · **Impacto:** medio — el piso se le informa mal al usuario.

`E213`, `E214`, `E215` y `E216` figuran con `piso: 1`, pero la numeración de la
facultad sugiere piso 2 (el `2` inicial). `E111` sí es consistente con piso 1.

**Qué hay que hacer:** confirmar en terreno y corregir el campo `piso`.

---

## D-03 · Cobertura del índice menor que la de la base de conocimiento

**Estado:** abierta · **Impacto:** medio — es la limitación M4 del proyecto.

La base menciona lugares que no son localizables en el plano: la "pajarera", el
CEC, la cafetería DeltaTe, la piscina, las áreas deportivas del piso −3, las
máquinas expendedoras, el Taller de los Dos Relojes, el CEIN, el Péndulo de
Foucault, la Terraza Ebria.

**Qué hay que hacer:** levantar las coordenadas y agregarlos, probablemente como
un archivo nuevo `data/lugares.json` con el mismo esquema de edificios y
`tipo: "servicio"`. Priorizar según las búsquedas fallidas del registro
(ver `OPERACION.md` §3), no por intuición.

---

## D-04 · El plano no coincide en proporción con el lienzo

**Estado:** abierta · **Impacto:** bajo — distorsión visual leve.

El PNG mide 812 × 1512 px (proporción 0,537) y el lienzo virtual es 1500 × 2756
(proporción 0,544). La imagen se estira ~1,3 % en horizontal. Es imperceptible y
las coordenadas existentes son consistentes con el lienzo.

**Qué hay que hacer:** al reemplazar el plano por uno de mejor resolución,
ajustar el lienzo a su proporción real **y reescalar todas las coordenadas** en
el mismo cambio.

---

## D-05 · Cobertura académica cargada a mano

**Estado:** abierta · **Impacto:** alto — es la limitación L1 del proyecto.

La base tiene 6 cursos y 2 perfiles docentes completos, de un catálogo de
cientos. Toda consulta fuera de ese conjunto queda sin respaldo, y lo cargado se
desactualiza cada semestre.

**Qué hay que hacer:** integración con U-Campus. Diseño en `ROADMAP.md` §1.
Requiere autorización institucional antes de cualquier implementación.

---

## D-06 · Correspondencia entre `B01`–`B08` y las salas del plano de planta -1

**Estado:** parcialmente resuelta (2026-09-15) · **Impacto:** bajo para
`B01`–`B08` (ya confirmado); alto para las 2 salas que faltan.

El plano de arquitectura del piso -1 (`007_SUBTE 1_PBP.dxf`, ver ADR-0009)
rotula sus salas de clase como "SALA DE CLASES 01" a "10", en dos pasillos
distintos (01–04 en uno, 05–10 en otro). Ninguna usa la nomenclatura "B" que sí
usa `data/salas.json` (`B01`–`B08`), y hay 10 salas dibujadas contra 8
registradas: no había forma de inferir la correspondencia desde el plano sin
arriesgar asignar mal una sala.

**Resuelto:** el equipo confirmó en terreno la correspondencia para `B01`–`B08`
(2026-09-15). Ya está en `data/salas.json` (`coord_interior`) y en
`data/plantas.json`:

| Código | Rótulo en el plano |
|---|---|
| B01 | SALA DE CLASES 04 |
| B02 | SALA DE CLASES 03 |
| B03 | SALA DE CLASES 02 |
| B04 | SALA DE CLASES 01 |
| B05 | SALA DE CLASES 10 |
| B06 | SALA DE CLASES 08 |
| B07 | SALA DE CLASES 07 |
| B08 | SALA DE CLASES 06 |

**Sigue abierto:** "SALA DE CLASES 05" y "SALA DE CLASES 09" no tienen código
`B` confirmado. El equipo mencionó "B09" para la 05 (con más confianza) y "B10"
para la 09 (dicho como intuición propia, explícitamente sin confirmar) — **no
se cargó ninguna de las dos** porque no cumplen el estándar de esta regla: un
dato con seguridad a medias se anota, no se escribe. Además, cada una de las 3
salas con forma de hexágono del plano (incluidas B05–B08) contiene **dos**
rótulos de "SALA DE CLASES" muy próximos entre sí — falta confirmar si son
de verdad dos salas separadas (un tabique al medio) o una sola sala con dos
números.

**Qué hay que hacer:** confirmar en terreno el código oficial de "SALA DE
CLASES 05" y "09", y si las salas pareadas en cada hexágono son una sala o
dos. Con eso, agregar las filas que falten a `data/salas.json`.

---

## Resueltas

| Id | Problema | Resuelto en |
|---|---|---|
| D-00a | Alias corruptos en `E111`, `E213`–`E216` (comillas tipográficas dentro del string) | v1.0.0 |
| D-00b | Alias `auditorio` ambiguo entre Gorbea (850) y d'Etigny (851) | v1.0.0 |
| D-00c | `GORBEA_SALA` duplicaba `850_AUDITORIO` compitiendo por la misma clave | v1.0.0 |
| D-00d | `piso` como texto en vez de entero | v1.0.0 |
