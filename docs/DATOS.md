# Datos del campus

Todo lo que la aplicación sabe vive en `data/`. Nada está escrito en el código.

```
data/
├── edificios.json    27 edificios, accesos y espacios con coordenada en el plano
├── salas.json        33 salas, con piso e instrucciones de acceso
├── plantas.json       planos interiores por piso (ver §6 y ADR-0009)
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
| `coord_interior` | `[y, x]` | no | Posición dentro del plano interior del piso, en **metros** (ver §6). Ausente mientras no se levante el dato |
| `poligono_interior` | lista de `[y, x]` | no | Contorno de la sala, mismo sistema. Solo si se pudo derivar con certeza del plano (ver §6) |

La sala hereda la coordenada de su edificio para el mapa exterior: esa vista
es cenital y no distingue pisos (limitación M1). La altura se comunica por
texto, salvo que exista un plano interior del piso (§6), en cuyo caso
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
exterior (no calzan sus coordenadas entre sí a propósito). Se dibuja **como
vector** —formas y símbolos—, no como imagen del plano de arquitectura.

```json
{
  "id": "851_SUBTE1",
  "acceso": "851",
  "piso": -1,
  "ancho_m": 101.82,
  "alto_m": 71.15,
  "puntos": [
    { "nombre": "PISCINA", "tipo": "piscina", "coord": [34.78, 19.15] }
  ],
  "fuente": "Plano de arquitectura piso -1 (...), extraído con scripts/extraer_planta_dxf.py",
  "activo": true
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | texto | sí | `MAYÚSCULAS_Y_GUION_BAJO`, único |
| `acceso` | enum | sí | `"850"` o `"851"` — junto con `piso`, identifica el plano |
| `piso` | entero | sí | El mismo número que usa `salas.json` |
| `ancho_m`, `alto_m` | número | sí | Tamaño real del piso en metros: envolvente de los muros |
| `geometria` | texto | no | Archivo GeoJSON en `assets/plantas/` con los recintos del piso. **Se genera, no se edita a mano** |
| `puntos` | lista | no | Referencias del piso (ver abajo) |
| `fuente` | texto | no | De dónde salió el plano y cómo se procesó |
| `activo` | booleano | no | `false` oculta la planta sin borrarla |

Cada elemento de `puntos` tiene `nombre` (el rótulo **tal cual** lo escribe el
plano, no uno inventado), `tipo` (`bano`, `piscina`, `camarin`, `ascensor`,
`escalera`) y `coord` `[y, x]` en metros.

**Sistema de coordenadas:** cada planta tiene el suyo, en metros, origen
abajo-izquierda (misma convención que el lienzo exterior: `y` crece hacia
arriba). No hay conversión entre el sistema de una planta y el lienzo exterior.
Los 13 pisos del 851 sí comparten origen entre sí, por venir del mismo proyecto
CAD (ver ADR-0009) — importa para cuando se agregue ruteo entre pisos.

### Cuidado con la escala del DXF

Los planos del 851 **están dibujados en centímetros aunque su encabezado
declara milímetros**. Creerle al encabezado da un edificio 10 veces más chico
(pasó: ver ACT-010). `scripts/extraer_planta_dxf.py` asume centímetros e
imprime medidas de control —ancho de puerta, espesor de muro— para
confirmarlo: **una puerta mide 0,8–1,1 m y un muro 0,2–0,3 m**. Si esos
números salen absurdos, la escala del archivo es otra.

### Los recintos: el piso completo

El plano **no trae las salas como figuras cerradas**: solo los trazos de sus
muros. `scripts/extraer_planta_dxf.py --recintos` los reconstruye: dibuja
muros, tabiques, puertas y ascensores sobre una grilla, busca las bolsas de
espacio que quedan cerradas entre ellos, y traza el contorno de cada una. El
resultado es un GeoJSON en `assets/plantas/` con un polígono por recinto
—sala, pasillo, hall, sala de máquinas—, en metros.

Los recintos que son salas del catálogo se sacan de ese archivo y su contorno
pasa a `poligono_interior` en `salas.json`: así el mapa sabe cuáles responden
al cursor y cuáles son solo fondo.

### Contornos: solo si son ciertos

Un contorno se carga **solo si se pudo derivar del plano**. `--recintos` lo
deriva de los muros; `--contorno` entrega un rectángulo solo si la sala es
rectangular de verdad (compara el área encerrada con la del rectángulo). Si no
se puede, la sala queda sin contorno y se dibuja como punto. Es la regla 3.1
aplicada a la geometría: mejor un punto correcto que una forma inventada.

### Agregar un piso nuevo

1. Conseguir el plano en **DXF** (no DWG — ver el encabezado de
   `scripts/extraer_planta_dxf.py` para cómo exportarlo).
2. `pip install ezdxf` (una vez; la aplicación no lo necesita).
3. Marco y referencias del piso:

   ```bash
   python scripts/extraer_planta_dxf.py plano.dxf --puntos
   ```

   Copiar `ancho_m`, `alto_m` y la lista de `puntos` a `data/plantas.json`.
   **Revisar la medida de control de la puerta antes de seguir.**
3b. Recintos del piso (necesita además `numpy`, `scipy` y `pillow`):

   ```bash
   python scripts/extraer_planta_dxf.py plano.dxf --recintos assets/plantas/<archivo>.geojson
   ```

   Anotar el nombre del archivo en el campo `geometria` de la planta.
4. Ubicar cada sala y sacar su contorno:

   ```bash
   python scripts/extraer_planta_dxf.py plano.dxf --buscar "SALA DE CLASES"
   python scripts/extraer_planta_dxf.py plano.dxf --contorno 19726,12016
   ```

   **Antes de escribirlo, confirmar con el equipo que el rótulo del plano
   corresponde de verdad al código oficial de la sala** (regla 3.1 — ver D-06
   en `docs/DEUDA_DATOS.md` para un caso real de esto).
5. `make validar` y `make test`.
6. Nota de actualización y CHANGELOG.

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
