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

## Resueltas

| Id | Problema | Resuelto en |
|---|---|---|
| D-00a | Alias corruptos en `E111`, `E213`–`E216` (comillas tipográficas dentro del string) | v1.0.0 |
| D-00b | Alias `auditorio` ambiguo entre Gorbea (850) y d'Etigny (851) | v1.0.0 |
| D-00c | `GORBEA_SALA` duplicaba `850_AUDITORIO` compitiendo por la misma clave | v1.0.0 |
| D-00d | `piso` como texto en vez de entero | v1.0.0 |
