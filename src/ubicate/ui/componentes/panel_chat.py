"""Panel de conversación."""

from __future__ import annotations

import streamlit as st

from ubicate.chat.prompts import SALUDO
from ubicate.ui import estado, recursos

AVATARES = {"user": "🧑‍🎓", "assistant": "🧭"}


def render() -> None:
    st.subheader("Pregúntame")
    conversacion = estado.conversacion()

    contenedor = st.container(height=420)
    with contenedor:
        if not conversacion.mensajes:
            with st.chat_message("assistant", avatar=AVATARES["assistant"]):
                st.markdown(SALUDO)
        for mensaje in conversacion.mensajes:
            with st.chat_message(mensaje.rol, avatar=AVATARES.get(mensaje.rol)):
                st.markdown(mensaje.texto)

    consulta = st.chat_input("¿Dónde almuerzo? ¿En qué sala es mi clase?")
    if not consulta:
        return

    settings = recursos.settings()
    veredicto = estado.permitir_mensaje(settings)
    if not veredicto.permitido:
        st.warning(veredicto.motivo)
        return

    estado.registrar_envio()
    conversacion.agregar("user", consulta)

    with contenedor:
        with st.chat_message("user", avatar=AVATARES["user"]):
            st.markdown(consulta)
        with st.chat_message("assistant", avatar=AVATARES["assistant"]):
            with st.spinner("Buscando…"):
                respuesta = recursos.motor().responder(consulta, conversacion)
            st.markdown(respuesta.texto)
            # Fuera de producción se muestra la causa real: si no, el usuario
            # solo ve "tuve un problema" y la causa queda enterrada en el log.
            if respuesta.error and settings.entorno.value != "produccion":
                st.error(
                    f"Detalle técnico ({respuesta.proveedor}): {respuesta.error}\n\n"
                    "Ejecuta `python scripts/probar_proveedor.py` para diagnosticarlo."
                )
            if respuesta.citas:
                with st.expander("De dónde saqué esto"):
                    for cita in respuesta.citas[:3]:
                        st.caption(f"· {cita}")

    conversacion.agregar("assistant", respuesta.texto)

    recursos.registro().registrar(
        sesion=estado.id_sesion(),
        origen="chat",
        consulta=consulta,
        estado="sin_respuesta" if respuesta.sin_respuesta else "respondido",
        destino_id=respuesta.destino.id if respuesta.destino else None,
        ms=respuesta.ms,
        proveedor=respuesta.proveedor,
    )

    # Puente automático chat → mapa (Objetivo 3).
    if respuesta.destino is not None:
        estado.fijar_destino(respuesta.destino.id)
        st.rerun()
