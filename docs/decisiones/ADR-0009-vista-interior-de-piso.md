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
   (`crs="Simple"`, imagen incrustada en base64, HTML autocontenido y
   cacheado). Se abre desde un desplegable en la ficha del destino
   (`panel_mapa.py`) cuando la sala tiene plano interior.
2. **Sistema de coordenadas propio de cada piso, en metros**, tal como sale
   del plano de arquitectura — sin intentar calzarlo con el lienzo exterior de
   1500×2756. `Sala.coord_interior` usa ese sistema local; `PlantaInterior`
   guarda el tamaño real (`ancho_m`, `alto_m`) y la imagen de fondo.
3. **Nuevo archivo `data/plantas.json`** y modelo `PlantaInterior` en
   `modelos.py`. Documentado en `docs/DATOS.md` §6.
4. **La extracción del DXF es una herramienta aparte**
   (`scripts/extraer_planta_dxf.py`), con `ezdxf` y `matplotlib` como
   dependencia opcional (`pip install .[planos]`) — nunca en tiempo de
   ejecución de la aplicación. Se corre una vez por piso; el resultado (PNG +
   coordenadas) es lo que se versiona, no el DWG/DXF original (son archivos
   pesados y no hacen falta después de extraídos).

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
