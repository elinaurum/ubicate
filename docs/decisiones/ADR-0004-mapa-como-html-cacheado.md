# ADR-0004 · Mapa como HTML cacheado, sin `streamlit-folium`

- **Estado:** aceptada
- **Fecha:** 2026-09-08

## Contexto

El prototipo usaba `st_folium`, que devuelve al servidor los eventos del mapa
(centro, zoom, clics). Cada arrastre o acercamiento provoca una re-ejecución
completa del script. Con un usuario es un detalle; con decenas simultáneas es
tráfico y CPU gastados en algo que la aplicación no usa, porque U-bícate no
necesita reaccionar a los clics en el plano.

Aparte, el plano no se veía: `ImageOverlay` apuntaba a `assets/mapa_beauchef.png`,
una ruta relativa que el navegador no puede resolver dentro del iframe donde se
monta el mapa.

## Decisión

1. `mapa/render.py` construye el mapa y devuelve **HTML autocontenido**.
2. La imagen del plano se incrusta como **data URI en base64**.
3. La interfaz lo muestra con `components.html`.
4. El HTML se memoriza con `@st.cache_data` por combinación destino × origen.

Se elimina la dependencia `streamlit-folium`.

## Consecuencias

**A favor**

- El plano se ve, que era el fallo de fondo.
- Acercar y desplazar ocurre entero en el navegador: cero viajes al servidor.
- Las combinaciones frecuentes se sirven ya construidas; el costo de armar los
  ~120 KB del mapa se paga una vez por combinación y no una por interacción.
- `render.py` es probable sin Streamlit.

**En contra**

- Se pierde la interacción de vuelta: no se puede saber en qué marcador hizo clic
  el usuario. Hoy no se usa. Si algún día se necesita, hay que reintroducir
  ``st_folium`` o un componente propio, y volver a evaluar este ADR.
- El HTML embebido pesa ~120 KB. Aceptable, y cacheado.
- La caché tiene TTL de una hora: si se reemplaza el plano en caliente, tarda
  hasta una hora en verse. En la práctica el plano cambia con el despliegue, que
  reinicia el proceso y vacía la caché.
