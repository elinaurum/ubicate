"""Punto de entrada de la aplicación Streamlit.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ubicate.datos.repositorio import ErrorDatos
from ubicate.ui import estado, recursos
from ubicate.ui.componentes import barra_lateral, panel_chat, panel_mapa

# Clave del widget de navegación. Es distinta de estado.Claves.VISTA a propósito:
# la fuente de verdad es el estado (la puede cambiar el chat al encontrar un
# lugar); este widget solo la refleja y se sincroniza en cada recarga.
_CLAVE_WIDGET_VISTA = "ub_vista_widget"

_ETIQUETA_VISTA = {estado.VISTA_CHAT: "💬 Preguntar", estado.VISTA_MAPA: "🗺️ Mapa"}


def main() -> None:
    st.set_page_config(
        page_title="U-bícate — FCFM Beauchef",
        page_icon="🧭",
        # Pensado para el teléfono: una sola columna centrada, sin la barra
        # lateral abierta tapando la pantalla al entrar.
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    try:
        recursos.repositorio()
    except ErrorDatos as exc:
        st.error("La aplicación no puede iniciar: los datos del campus tienen errores.")
        for problema in exc.problemas:
            st.write(f"- {problema}")
        st.stop()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    estado.inicializar()
    barra_lateral.render()

    st.title("U-bícate")
    st.caption(
        "Pregunta en lenguaje natural o busca directamente en el plano. "
        "Respondo solo con información verificada de la FCFM."
    )

    # Navegación entre las dos vistas. Se copia el estado al widget ANTES de
    # crearlo (única forma admitida de fijar su valor); así, cuando el chat
    # cambia la vista a "mapa", el selector aparece ya en esa posición.
    st.session_state[_CLAVE_WIDGET_VISTA] = estado.vista()
    eleccion = st.segmented_control(
        "Vista",
        options=[estado.VISTA_CHAT, estado.VISTA_MAPA],
        format_func=_ETIQUETA_VISTA.get,
        key=_CLAVE_WIDGET_VISTA,
        label_visibility="collapsed",
        width="stretch",
    )
    vista_actual = eleccion or estado.vista()
    estado.fijar_vista(vista_actual)

    if vista_actual == estado.VISTA_MAPA:
        panel_mapa.render()
    else:
        panel_chat.render()


if __name__ == "__main__":
    main()
