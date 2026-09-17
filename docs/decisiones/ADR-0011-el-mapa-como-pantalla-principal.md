# ADR-0011 · El mapa como pantalla principal, el chat detrás de la mascota

- **Estado:** aceptada
- **Fecha:** 2026-09-17
- **Supera a:** [ADR-0006](ADR-0006-navegacion-una-vista-a-la-vez.md) en el
  **control** de navegación. Mantiene intacto su fundamento: una sola vista a
  la vez, pensada para el teléfono.
- **Relacionado:** [ADR-0007](ADR-0007-varios-lugares-con-botones.md) (los
  botones de lugar del chat siguen llevando al mapa)

## Contexto

ADR-0006 reemplazó las dos columnas por **una vista a la vez**, con un selector
arriba (`st.segmented_control`): "💬 Preguntar" / "🗺️ Mapa". La vista que se
abría primero era el chat.

El equipo entregó la maqueta completa de la aplicación y pidió seguirla. Su
navegación es distinta:

- el **mapa es la pantalla principal**, con el buscador arriba;
- al chat se entra por un **botón con la mascota**;
- del chat se vuelve con una **flecha**.

No hay selector de vistas en ninguna pantalla de la maqueta.

## Decisión

1. **El mapa es la vista inicial.** `estado.inicializar()` abre en
   `VISTA_MAPA`, y también ahí vuelve `estado.salir()`.
2. **Se elimina el selector.** `app.py` despacha según `estado.vista()`; cada
   panel pone su propia salida.
3. **Del mapa al chat:** botón "Pregúntame lo que necesites", con la mascota.
4. **Del chat al mapa:** botón "← Volver al mapa".
5. **Los botones de lugar del chat siguen cambiando a la vista del mapa**, como
   define ADR-0007. Esa parte no cambia.

### Lo que no se copió literal de la maqueta, y por qué

- **El botón de la mascota va arriba, bajo el buscador, no flotando abajo.** En
  la maqueta flota sobre el plano. En la aplicación real el plano es alto: ahí
  abajo el botón queda fuera de pantalla y hay que desplazarse para encontrarlo.
  Se comprobó en el navegador antes de decidirlo.
- **Es un botón con texto, no un círculo con solo la imagen.** Un botón sin
  texto no se puede etiquetar para lectores de pantalla desde Streamlit. Con
  texto lo entiende cualquiera, y la mascota igual aparece.

## Alternativas consideradas

1. **Dejar el selector y solo cambiar el orden.** Menos trabajo, pero deja en
   pantalla un control que la maqueta no tiene y que compite con el buscador.
2. **Copiar el botón flotante tal cual.** Exige CSS pegajoso sobre el
   contenedor de desplazamiento de Streamlit, que es frágil, y deja un botón
   sin texto. Se prefirió que funcione y se entienda.

## Consecuencias

**A favor**

- Quien entra ve el mapa, que es a lo que viene la mayoría: ubicar algo.
- Una pantalla menos cargada: el buscador manda, y el chat es una acción clara.
- Sigue habiendo una sola vista a la vez, que es lo que ADR-0006 resolvió y no
  se toca.

**En contra**

- Llegar al chat es un toque más que antes para quien venía a preguntar. Es el
  precio de que el mapa sea lo primero.
- La mascota es un archivo en `assets/`, no código: si falta, el botón se ve
  sin imagen. Está resuelto para que no rompa nada, pero es una dependencia de
  contenido que antes no existía.
