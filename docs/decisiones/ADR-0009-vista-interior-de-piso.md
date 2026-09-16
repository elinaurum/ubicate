# ADR-0009 · Vista interior de piso, separada del mapa exterior

- **Estado:** aceptada
- **Fecha:** 2026-09-15
- **Relacionado:** ADR-0004 (mismo patrón de HTML cacheado), `docs/ROADMAP.md`
  §7 (mapa 3D con ruteo interior — esta es su primera parte, sin ruteo)

## Contexto

El equipo consiguió los planos de arquitectura (DWG, uno por piso) del
edificio 851: 13 archivos, de subterráneo 6 a piso 7. El mapa actual
(`assets/mapa_beauchef.png`) es una vista cenital de todo el campus con un
marcador por edificio; no distingue pisos (limitación M1, ver `docs/DATOS.md`
§3). Los planos DWG sí traen el detalle interior real: muros, puertas,
ascensores y el nombre de cada sala.

Se partió por el piso -1, que es donde están las 8 salas `B01`–`B08` ya
registradas en `data/salas.json`.

Dos hallazgos del trabajo exploratorio, antes de decidir:

1. **Los 13 DXF comparten el mismo origen de coordenadas** (mismo `$EXTMIN` en
   los 13 archivos): vienen del mismo proyecto CAD, así que los pisos ya
   calzan entre sí sin ningún ajuste. Sirve para cuando se agregue ruteo entre
   pisos (roadmap §7 paso 1).
2. **El plano no rotula las salas como "B01"–"B08"**: usa "SALA DE CLASES
   01"–"10" (dos pasillos, 10 salas dibujadas contra 8 registradas). La
   correspondencia la confirmó el equipo en terreno, no se dedujo del plano
   (regla 3.1 de `CLAUDE.md`) — ver `docs/DEUDA_DATOS.md` D-06.

## Decisión

1. **Vista exclusiva por piso**, no una capa más del mapa exterior. Es un
   mapa folium propio (`mapa/interior.py`), con el mismo patrón del ADR-0004
   (`crs="Simple"`, HTML autocontenido y cacheado). Se abre desde un
   desplegable en la ficha del destino (`panel_mapa.py`) cuando la sala tiene
   plano interior.
2. **Sistema de coordenadas propio de cada piso, en metros**, tal como sale
   del plano de arquitectura — sin intentar calzarlo con el lienzo exterior de
   1500×2756. `Sala.coord_interior` usa ese sistema local; `PlantaInterior`
   guarda el tamaño real del piso (`ancho_m`, `alto_m`) y sus referencias.
3. **Nuevo archivo `data/plantas.json`** y modelo `PlantaInterior` en
   `modelos.py`. Documentado en `docs/DATOS.md` §6.
4. **Se dibuja el piso completo como vector, no como imagen del plano CAD.**
   Cada recinto —sala, pasillo, hall, baño, sala de máquinas— es una figura
   con su borde y su relleno, con la forma que tiene en el plano. El dibujo de
   arquitectura trae cotas, ductos, pilotes y rótulos de construcción que
   estorban a quien solo quiere ubicarse, y su paleta es técnica, no de
   producto.
5. **Los recintos se reconstruyen desde los muros.** El plano no trae las
   salas como figuras cerradas, así que se dibujan muros, tabiques, puertas y
   ascensores sobre una grilla, se buscan las bolsas de espacio cerradas entre
   ellos y se traza el contorno de cada una
   (`scripts/extraer_planta_dxf.py --recintos`). El resultado vive en un
   GeoJSON en `assets/plantas/`, referenciado desde `PlantaInterior.geometria`.
6. **Todo gris; el verde es del cursor.** El piso entero se dibuja en grises.
   El verde queda reservado para una sola cosa: indicar que el cursor está
   sobre un destino. Así el color significa algo en vez de decorar.
7. **Un contorno solo se dibuja si es cierto.** Si un recinto no se puede
   derivar del plano, la sala queda sin contorno y se dibuja como punto. Es la
   regla 3.1 aplicada a la geometría: mejor un punto correcto que una forma
   inventada.
8. **La extracción del DXF es una herramienta aparte**
   (`scripts/extraer_planta_dxf.py`), con `ezdxf` como dependencia opcional
   (`pip install .[planos]`) — nunca en tiempo de ejecución de la aplicación.
   Se corre una vez por piso; el resultado (medidas y coordenadas) es lo que
   se versiona, no el DWG/DXF original (son archivos pesados y no hacen falta
   después de extraídos).

## Alternativas consideradas

1. **Calzar el piso interior con el lienzo exterior (una sola capa por
   piso).** Exige georreferenciar cada planta contra el plano cenital
   (roadmap §7 paso 1 leído en ese sentido). No hace falta para esta primera
   entrega: el objetivo es "cómo es el piso por dentro", no "dónde cae visto
   desde arriba". Se descarta por ahora; si se necesita más adelante (por
   ejemplo, para una ruta que empieza en la calle y termina en una sala), se
   revisa este ADR — para eso sirve que los 13 pisos ya compartan origen.
2. **Construir de una vez el ítem completo del roadmap (grafo + ruteo).**
   Mucho más grande de lo que pide esta entrega. Se prefieren cambios
   acotados: esta vista deja el modelo de datos listo para que el ruteo se
   agregue después sin rehacerlo.
3. **Incrustar el dibujo del plano como imagen de fondo.** Fue la primera
   versión y se descartó tras verla: se ve como un plano de obra (colores por
   capa técnica, cotas, ductos), pesa ~120 KB en base64 por piso, y no deja
   resaltar una sala ni distinguir un baño de un ascensor.
4. **Dibujar solo las salas del catálogo, sobre fondo vacío.** Fue la segunda
   versión y el equipo la rechazó: sin el resto del piso, las salas quedan
   flotando y no se entiende dónde están. El piso hay que modelarlo entero.
5. **Dibujar los muros como líneas, sin recintos.** Fiel al trazado y barato
   (235 KB de líneas), pero se lee como un plano técnico, no como un mapa, y
   no permite que una sala responda al cursor. Los recintos pesan menos
   (46 KB) y sí son figuras.

## Consecuencias

**A favor**

- El piso -1 ya se puede ver por dentro, con las 8 salas B ubicadas con datos
  reales del plano de arquitectura, no aproximados.
- El modelo de datos (`PlantaInterior`, `coord_interior`) sirve tal cual para
  los otros 12 pisos: agregar uno es correr el script y sumar filas a
  `plantas.json`/`salas.json`.
- `mapa/interior.py` no importa Streamlit: se prueba sin la aplicación
  (`tests/test_mapa_interior.py`), igual que `mapa/render.py`.

**En contra**

- No hay todavía forma de ir "de la calle a la sala" en un solo plano: el
  usuario ve el mapa exterior y, aparte, el interior. Es la limitación que
  esta entrega no resuelve (queda para cuando se aborde el ruteo).
- Dos salas del piso -1 ("SALA DE CLASES 05" y "09") quedaron fuera de
  `salas.json`: el equipo no tiene aún su código oficial confirmado
  (`docs/DEUDA_DATOS.md` D-06). El plano interior no las muestra hasta que se
  resuelva.
- Los DWG/DXF originales no quedan en el repositorio (pesan varios MB cada
  uno). Si hace falta reprocesar un piso con otras capas, hay que volver a
  pedirlos.
- La reconstrucción pasa por una grilla de 5 cm, así que los bordes tienen
  una precisión de ese orden y se enderezan los tramos casi rectos. Para
  ubicarse es de sobra; no sirve para medir ni para un plano de obra.
- Un recinto se reconstruye solo si queda **cerrado** por muros o puertas. Un
  espacio abierto a un pasillo se funde con él en una sola figura: por eso hay
  un recinto grande de ~850 m² que es todo el sistema de circulación.
- El GeoJSON se genera, no se edita a mano. Si cambia el plano hay que volver
  a correr el script; no tiene sentido corregirlo a mano vértice por vértice.
