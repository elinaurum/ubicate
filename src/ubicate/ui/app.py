"""Punto de entrada de la aplicación Streamlit.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ubicate.datos.repositorio import ErrorDatos
from ubicate.ui import estado, recursos
from ubicate.ui.componentes import barra_lateral, panel_chat, panel_mapa

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

    # Navegación entre las dos vistas. La fuente de verdad es el estado de
    # sesión, no el widget: el chat puede cambiar la vista a "mapa" al encontrar
    # un lugar. Para que el selector siga a ese cambio sin pelear con Streamlit,
    # su `key` incluye la vista actual: cuando el estado cambia, el widget se
    # reconstruye y toma `default`. Cuando es el usuario quien pulsa, la
    # elección difiere del estado y lo actualizamos.
    vista_actual = estado.vista()
    eleccion = st.segmented_control(
        "Vista",
        options=[estado.VISTA_CHAT, estado.VISTA_MAPA],
        format_func=_ETIQUETA_VISTA.get,
        default=vista_actual,
        key=f"ub_vista_widget_{vista_actual}",
        label_visibility="collapsed",
        width="stretch",
    )
    if eleccion and eleccion != vista_actual:
        estado.fijar_vista(eleccion)
        st.rerun()

    if vista_actual == estado.VISTA_MAPA:
        panel_mapa.render()
    else:
        panel_chat.render()


if __name__ == "__main__":
    main()
