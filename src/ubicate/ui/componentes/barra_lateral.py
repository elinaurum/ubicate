"""Barra lateral: punto de partida, acciones y estado del sistema."""

from __future__ import annotations

import streamlit as st

from ubicate import __version__
from ubicate.ui import estado, recursos


def render() -> None:
    repo = recursos.repositorio()
    settings = recursos.settings()

    with st.sidebar:
        st.markdown("### U-bícate")
        st.caption("Orientación e información del campus FCFM Beauchef")

        # El selector de "¿dónde estás ahora?" vive junto al mapa (panel_mapa):
        # es parte del flujo de la ruta, no un ajuste de sistema, y en el
        # teléfono la barra lateral queda escondida tras el menú.

        st.divider()
        if st.button("Reiniciar conversación", use_container_width=True):
            estado.limpiar_conversacion()
            estado.limpiar()
            st.rerun()

        st.divider()
        diagnostico = repo.diagnostico
        kb = recursos.conocimiento()
        st.caption(
            f"v{__version__} · {diagnostico.edificios} edificios · "
            f"{diagnostico.salas} salas · {len(kb.fragmentos)} fragmentos"
        )
        st.caption(f"Modelo: {recursos.motor().proveedor}")

        if kb.vencidos:
            st.warning(
                "Hay contenido con vigencia vencida: "
                + ", ".join(d.id for d in kb.vencidos)
            )
        if diagnostico.conflictos:
            st.warning(f"{len(diagnostico.conflictos)} conflictos de alias en los datos")

        if settings.entorno.value != "produccion":
            st.caption(f"Entorno: {settings.entorno.value}")
