# ADR-0006 · Navegación de una vista a la vez, orientada al teléfono

- **Estado:** aceptada
- **Fecha:** 2026-09-08
- **Reemplaza a:** — (el layout de dos paneles nunca tuvo ADR propio; se
  describía solo en `docs/ARQUITECTURA.md`, que se actualiza con este cambio)

La regla de capas del ADR-0001 sigue intacta: este cambio ocurre entero dentro
de `src/ubicate/ui/`.

## Contexto

La aplicación mostraba el chat y el mapa juntos: dos columnas
(`st.columns([1, 1.15])`), barra lateral abierta al entrar y `layout="wide"`.

El uso real es de pie, caminando por el campus, con el teléfono en la mano
(`docs/ROADMAP.md` §5). En esa pantalla el diseño fallaba:

- Streamlit apila las columnas en vertical. Quedaba el chat con su scroll
  interno y, mucho más abajo, el buscador, la ficha y el plano.
- El puente chat → mapa (Objetivo 3: la respuesta del asistente enciende el
  marcador) quedaba fuera de pantalla. El estudiante preguntaba "¿dónde es mi
  clase?", recibía la respuesta y no veía que el plano había reaccionado.
- La barra lateral abierta tapaba toda la pantalla al cargar, y el selector de
  punto de partida quedaba escondido tras el menú hamburguesa.

## Alternativas consideradas

1. **Pestañas (`st.tabs`).** Simples de entender, pero Streamlit no permite
   cambiar la pestaña activa desde el servidor. El chat no podría llevar al
   usuario al mapa al encontrar un lugar: se perdía el puente.
2. **Dejar todo apilado, solo compactado.** Menos cambio, pero el scroll largo y
   el salto que deja mirando texto siguen ahí.
3. **Layout adaptable: lado a lado en pantalla grande, vista única en el
   teléfono.** Exige medir el ancho del navegador con un componente extra —
   más piezas móviles y una dependencia más que mantener— para un público que
   usa la herramienta casi siempre desde el teléfono.

## Decisión

Una sola vista a la vez, con un selector (`st.segmented_control`) arriba:
**💬 Preguntar** / **🗺️ Mapa**. Igual en todos los tamaños de pantalla;
en computador se ve una columna centrada.

- `layout="centered"`, `initial_sidebar_state="collapsed"`.
- La vista activa vive en el estado de sesión (`estado.VISTA`), no en el widget.
  Al fijar un destino, `estado.fijar_destino` cambia la vista a `mapa`: el
  puente chat → mapa ahora **lleva** al usuario al plano en vez de actualizarlo
  fuera de su vista.
- El selector "¿dónde estás ahora?" pasa de la barra lateral al panel del mapa,
  junto al buscador, dentro de un desplegable. Es parte del flujo de la ruta.
- La barra lateral queda solo para lo secundario: reiniciar la conversación,
  versión y diagnóstico de datos, avisos de contenido vencido.

Piso de `streamlit` sube a `>=1.50` (`st.segmented_control` y su parámetro
`width`).

## Consecuencias

**A favor**

- Cada panel usa toda la pantalla: sin scroll largo, sin columnas apiladas.
- El puente chat → mapa se ve: es la interacción central de la herramienta.
- El punto de partida está donde se usa.
- Un solo camino de código y un solo comportamiento para todos los tamaños.

**En contra**

- En computador ya no se ven el chat y el mapa a la vez. Para el público
  objetivo —teléfono— es la decisión correcta; si algún día pesa el uso de
  escritorio, este ADR se revisa.
- La vista activa es un estado más que mantener sincronizado entre el widget y
  `estado`. Se resuelve copiando el estado al widget antes de crearlo, que es la
  única forma admitida por Streamlit de fijar su valor.
- `st.segmented_control` obliga a Streamlit ≥ 1.50 (antes ≥ 1.36).
