"""Pantallas de carga: la portada y la bienvenida (maqueta, láminas 2 y 6).

Cada una se muestra **una sola vez por sesión**: la portada antes de pedir la
clave, y la bienvenida justo después de entrar.

Son una **capa fija encima de todo que se desvanece sola** con una animación
de CSS, no una pausa del servidor. Se probaron las dos formas: con
`time.sleep` la sesión queda bloqueada y, peor, Streamlit deja a la vista en
gris lo de la pasada anterior mientras dura la espera, así que se veía el
formulario de acceso por debajo de la bienvenida (ACT-015). Con la capa, la
aplicación carga por detrás mientras se ve la portada, que es justamente lo
que se espera de una pantalla de carga.
"""

from __future__ import annotations

import streamlit as st

from ubicate.ui import estado, recursos, tema


def portada() -> None:
    """Chincheta y nombre, sobre la pantalla de acceso."""
    st.markdown(tema.portada(), unsafe_allow_html=True)
    estado.marcar_portada_vista()


def bienvenida() -> None:
    """Saludo con la mascota, sobre la aplicación recién cargada."""
    st.markdown(tema.bienvenida(recursos.settings().dir_assets), unsafe_allow_html=True)
    estado.marcar_bienvenida_vista()
