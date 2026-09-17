"""Punto de entrada de la aplicación Streamlit.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ubicate.acceso import Rol
from ubicate.datos.repositorio import ErrorDatos
from ubicate.ui import estado, recursos, tema
from ubicate.ui.componentes import (
    barra_lateral,
    panel_chat,
    panel_mapa,
    pantalla_acceso,
    pantalla_carga,
)


def main() -> None:
    st.set_page_config(
        page_title="U-bícate — FCFM Beauchef",
        page_icon="🧭",
        # Pensado para el teléfono: una sola columna centrada, sin la barra
        # lateral abierta tapando la pantalla al entrar.
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    estado.inicializar()

    # Portada, una vez por visita, antes de pedir la clave (maqueta, lámina 2).
    # No corta la pasada: se borra sola y sigue lo que venga abajo.
    if not estado.portada_vista():
        pantalla_carga.portada()

    # Puerta de acceso (ADR-0010). Va antes de cargar nada: quien no entró no
    # ve la aplicación ni sus posibles errores de datos. No es autenticación,
    # es una clave compartida mientras no haya cuentas.
    if recursos.settings().acceso_activo and estado.rol() is None:
        pantalla_acceso.render()
        return

    # Bienvenida, apenas se entra (maqueta, lámina 6).
    if not estado.bienvenida_vista():
        pantalla_carga.bienvenida()
    if not recursos.settings().acceso_activo and estado.rol() is None:
        estado.fijar_rol(Rol.USUARIO)

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

    barra_lateral.render()

    st.markdown(tema.CSS, unsafe_allow_html=True)
    st.markdown(tema.cabecera(), unsafe_allow_html=True)
    st.markdown(
        '<div class="ub-bajada">Pregunta en lenguaje natural o busca en el plano. '
        "Respondo solo con información verificada de la FCFM.</div>",
        unsafe_allow_html=True,
    )

    # Navegación (ADR-0011): el mapa es la pantalla principal y al chat se
    # entra desde el botón de la mascota. Cada panel pone su propia salida, así
    # que aquí solo se despacha lo que diga el estado.
    vista_actual = estado.vista()

    if vista_actual == estado.VISTA_MAPA:
        panel_mapa.render()
    else:
        panel_chat.render()


if __name__ == "__main__":
    main()
