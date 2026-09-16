# Datos del campus

Todo lo que la aplicación sabe vive en `data/`. Nada está escrito en el código.

```
data/
├── edificios.json    27 edificios, accesos y espacios con coordenada en el plano
├── salas.json        33 salas, con piso e instrucciones de acceso
├── plantas.json       planos interiores por piso (ver §7 y ADR-0009)
└── kb/               Base de conocimiento en Markdown con metadatos
```

## 1. `edificios.json`

```json
{
  "id": "850_FIS",
  "nombre": "Física",
  "tipo": "edificio",
  "acceso": "850",
  "coord": [1202, 506],
  "aliases": ["fisica"],
  "descripcion": "Departamento de Física. Acceso por Beauchef 850.",
  "activo": true
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | texto | sí | `MAYÚSCULAS_Y_GUION_BAJO`, único, estable. No se renombra: se usa en enlaces y métricas |
| `nombre` | texto | sí | Como lo dice la gente |
| `tipo` | enum | no | `edificio`, `acceso`, `servicio`, `deportivo`, `espacio_abierto` |
| `acceso` | enum | sí | `"850"` o `"851"`. Determina desde qué portería parte la ruta |
| `coord` | `[y, x]` | sí | Coordenada en el lienzo. **Primero y, después x** |
| `aliases` | lista | no | Solo alias con significado propio (ver §4) |
| `descripcion` | texto | no | Se muestra en la ficha y en el globo del mapa |
| `activo` | booleano | no | `false` oculta el registro sin borrarlo |

## 2. `salas.json`

```json
{
  "id": "B04",
  "edificio_id": "851_INDUS",
  "piso": -1,
  "tipo": "clase",
  "aliases": [],
  "instrucciones": "Entra por Beauchef 851, baja al piso -1 y sigue la señalética de salas B.",
  "activo": true
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | texto | sí | Código oficial de la sala |
| `edificio_id` | texto | sí | Debe existir en `edificios.json`, o la app no arranca |
| `piso` | entero | sí | Negativo para subterráneos. **Entero, no texto** |
| `tipo` | enum | no | `clase`, `auditorio`, `laboratorio`, `estudio` |
| `instrucciones` | texto | sí | Cómo llegar desde el acceso, en segunda persona |
| `coord_interior` | `[y, x]` | no | Posición dentro del plano interior del piso, en **metros** (ver §7). Ausente mientras no se levante el dato |

La sala hereda la coordenada de su edificio para el mapa exterior: esa vista
es cenital y no distingue pisos (limitación M1). La altura se comunica por
texto, salvo que exista un plano interior del piso (§7), en cuyo caso
`coord_interior` la ubica de verdad dentro de esa vista aparte.

## 3. Sistema de coordenadas

Las coordenadas están expresadas sobre un **lienzo virtual de 1500 × 2756**,
que no coincide con el tamaño en píxeles del PNG (812 × 1512). El plano se estira
para llenar ese lienzo, así que las coordenadas existentes siguen siendo válidas.

Las dimensiones están en `config.py` (`lienzo_ancho`, `lienzo_alto`). **Si se
cambia el lienzo hay que reescalar todas las coordenadas**, porque están
expresadas en sus unidades.

El origen `[0, 0]` está abajo a la izquierda: `y` crece hacia arriba. Es la
convención de folium con `crs="Simple"`.

### Cómo obtener la coordenada de un lugar nuevo

1. Abrir `assets/mapa_beauchef.png` en un editor de imágenes.
2. Ubicar el punto y anotar sus píxeles `(px, py)` desde la esquina **superior**
   izquierda.
3. Convertir:

   ```
   x = px * 1500 / 812
   y = 2756 - (py * 2756 / 1512)
   ```

4. Agregar el registro y verificar en la aplicación que el marcador cae donde debe.

## 4. Alias: cuándo agregarlos

**No hace falta agregar variantes ortográficas.** La normalización ya colapsa
mayúsculas, tildes, guiones, puntos y espacios: `B-04`, `b 04`, `sala B04` y
`B04` caen todos en la misma clave. Agregar `["b04", "B-04", "B 04"]` es ruido.

Un alias se agrega **solo cuando aporta una palabra distinta**: cómo le dice la
gente al lugar y no se deduce de su nombre.

* Sí: `"pajarera"` para el hall sur, `"comesanito"` para el casino Domeyko,
  `"la araña"` para el auditorio d'Etigny, `"csn"` para el Centro Sismológico.
* No: `"850_fisica"` para `850_FIS`, `"F-21"` para `F21`.

Un alias que apunte a dos lugares distintos hace fallar `make validar`. Si dos
lugares comparten de verdad un nombre coloquial, la interfaz pregunta cuál —
eso es correcto y no hay que "arreglarlo" borrando uno.

## 5. Base de conocimiento (`data/kb/`)

Cada archivo Markdown lleva una cabecera de metadatos:

```markdown
---
id: vida_en_campus
titulo: Vida cotidiana, servicios y espacios del campus
bloque: A
fuente: levantamiento del equipo U-bícate sobre canales institucionales FCFM
actualizado: 2026-09-08
vigencia: revisar_semestral
---
```

| Campo | Para qué |
|---|---|
| `id` | Identificador estable, se usa en las citas |
| `titulo` | Lo que ve el usuario al abrir "de dónde saqué esto" |
| `bloque` | Bloque temático A–J de la documentación del proyecto |
| `fuente` | De dónde salió. Sin fuente no entra a la base |
| `actualizado` | Fecha de la última revisión |
| `vigencia` | `permanente`, `revisar_semestral` o `vence:AAAA-MM-DD` |

`vigencia: vence:AAAA-MM-DD` es la respuesta a la limitación L2 del proyecto
("información con fecha de vencimiento"). Pasada la fecha:

* `make validar` lo reporta;
* la barra lateral lo muestra como advertencia;
* el fragmento llega al modelo marcado como posiblemente vencido, y el prompt le
  ordena advertirlo en la respuesta.

Úsalo en todo dato con fecha: plazos de elimina especial, precios del casino,
horarios de atención, procesos con ventana temporal.

**Fragmentación:** cada párrafo separado por línea en blanco es un fragmento
recuperable de forma independiente. En la práctica, escribe un párrafo por tema
y empiézalo con el título en negrita. Los párrafos de menos de 60 caracteres se
unen al siguiente.

**Títulos de fragmento:** el título es lo que más pesa en la búsqueda. Que
contenga las palabras del *tema* ("Espacios para estudiar", "Franquicia
dental"), no las de la *pregunta*. La recuperación ignora "dónde", "puedo",
"cómo", "hay", "cuál" y similares (lista en `chat/conocimiento.py`,
`VACIAS_TEXTO`): un título como "¿Dónde puedo estudiar?" se busca solo por
"estudiar".

## 6. Planos interiores (`data/plantas.json`)

Ver ADR-0009. Es la vista "cómo es este piso por dentro", separada del mapa
exterior (no calzan sus coordenadas entre sí a propósito).

```json
{
  "id": "851_SUBTE1",
  "acceso": "851",
  "piso": -1,
  "imagen": "851_piso_-1.png",
  "ancho_m": 49.65,
  "alto_m": 12.70,
  "fuente": "Plano de arquitectura piso -1 (...), extraído con scripts/extraer_planta_dxf.py",
  "activo": true
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | texto | sí | `MAYÚSCULAS_Y_GUION_BAJO`, único |
| `acceso` | enum | sí | `"850"` o `"851"` — junto con `piso`, identifica el plano |
| `piso` | entero | sí | Debe existir al menos una sala con ese `piso` para el mismo acceso |
| `imagen` | texto | sí | Nombre de archivo en `assets/plantas/` (no una ruta completa) |
| `ancho_m`, `alto_m` | número | sí | Tamaño real del plano en metros, tal como lo imprime `scripts/extraer_planta_dxf.py` |
| `fuente` | texto | no | De dónde salió el plano y cómo se procesó |
| `activo` | booleano | no | `false` oculta la planta sin borrarla |

**Sistema de coordenadas:** cada planta tiene el suyo, en metros, origen
abajo-izquierda (igual convención que el lienzo exterior: `y` crece hacia
arriba). No hay conversión entre el sistema de una planta y el lienzo
exterior ni entre plantas de distinto piso — cada una es independiente, salvo
que, por venir del mismo proyecto CAD, los 13 pisos de 851 comparten el mismo
origen entre sí (ver ADR-0009), lo que interesa para cuando se agregue ruteo
entre pisos.

### Agregar un piso nuevo

1. Conseguir el plano en **DXF** (no DWG — ver `scripts/extraer_planta_dxf.py`
   para cómo exportarlo).
2. `pip install ezdxf matplotlib` (una vez; no se necesita para correr la
   aplicación).
3. `python scripts/extraer_planta_dxf.py plano.dxf --salida assets/plantas/<archivo>.png`
   — copia el `ancho_m`/`alto_m` que imprime.
4. Agregar la entrada en `data/plantas.json` con esos valores.
5. Para cada sala de ese piso: `python scripts/extraer_planta_dxf.py plano.dxf --buscar "<texto del plano>"`
   para obtener su `coord_interior`. **Antes de escribirlo, confirmar con el
   equipo que el rótulo del plano corresponde de verdad al código oficial de
   la sala** (regla 3.1 — no inventar la correspondencia; ver D-06 en
   `docs/DEUDA_DATOS.md` para un caso real de esto).
6. `make validar` y `make test`.
7. Nota de actualización y CHANGELOG.

## 7. Agregar contenido: procedimiento

### Una sala nueva

1. Agregar el objeto en `data/salas.json`.
2. `make validar`
3. `make test`
4. Verificar en la aplicación que la búsqueda la encuentra y el marcador cae bien.
5. Nota en `docs/actualizaciones/` y entrada en el CHANGELOG (versión de parche).

### Un contenido nuevo en la base de conocimiento

1. Editar el archivo de `data/kb/` que corresponda, o crear uno nuevo con cabecera.
2. Actualizar el campo `actualizado`.
3. Poner `vigencia` con fecha si el dato tiene plazo.
4. `make validar` y probar la pregunta real en la aplicación.
5. Nota y CHANGELOG.

> El documento maestro original quedó en `scripts/_kb_origen.md` y `make kb` lo
> regenera. **Si editas `data/kb/` a mano, no vuelvas a correr `make kb`**: te
> sobreescribe los cambios. A partir de la v1.0.0 la fuente de verdad es
> `data/kb/`; el script es solo el registro de la importación inicial.
