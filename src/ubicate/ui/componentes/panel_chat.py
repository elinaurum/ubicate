"""Panel de conversación."""

from __future__ import annotations

import streamlit as st

from ubicate.chat.motor import Conversacion
from ubicate.chat.prompts import SALUDO
from ubicate.ui import estado, recursos

AVATARES = {"user": "🧑‍🎓", "assistant": "🧭"}


def _citas(mensaje) -> None:
    if mensaje.citas:
        with st.expander("De dónde saqué esto"):
            for cita in mensaje.citas[:3]:
                st.caption(f"· {cita}")


def _botones_mapa(conversacion: Conversacion) -> None:
    """Un botón por cada lugar de la última respuesta del asistente.

    No se salta al mapa solo: es el usuario quien elige qué lugar abrir, porque
    una misma consulta puede sugerir más de uno (ver ADR-0007).
    """
    ultimo = next(
        (m for m in reversed(conversacion.mensajes) if m.rol == "assistant"), None
    )
    if ultimo is None or not ultimo.lugares:
        return

    repo = recursos.repositorio()
    destinos = [d for d in (repo.destino(lid) for lid in ultimo.lugares) if d is not None]
    if not destinos:
        return

    st.caption("¿Te lo muestro en el mapa?")
    columnas = st.columns(min(len(destinos), 3))
    for i, destino in enumerate(destinos):
        if columnas[i % len(columnas)].button(
            f"📍 {destino.etiqueta_corta}",
            key=f"ver_mapa_{destino.id}",
            use_container_width=True,
        ):
            estado.fijar_destino(destino.id)
            estado.fijar_vista(estado.VISTA_MAPA)
            st.rerun()


def render() -> None:
    st.subheader("Pregúntame")
    conversacion = estado.conversacion()

    contenedor = st.container(height=460)
    with contenedor:
        if not conversacion.mensajes:
            with st.chat_message("assistant", avatar=AVATARES["assistant"]):
                st.markdown(SALUDO)
        for mensaje in conversacion.mensajes:
            with st.chat_message(mensaje.rol, avatar=AVATARES.get(mensaje.rol)):
                st.markdown(mensaje.texto)
                if mensaje.rol == "assistant":
                    _citas(mensaje)

    _botones_mapa(conversacion)

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

    conversacion.agregar(
        "assistant",
        respuesta.texto,
        citas=tuple(respuesta.citas),
        lugares=tuple(d.id for d in respuesta.destinos),
    )

    recursos.registro().registrar(
        sesion=estado.id_sesion(),
        origen="chat",
        consulta=consulta,
        estado="sin_respuesta" if respuesta.sin_respuesta else "respondido",
        destino_id=respuesta.destino.id if respuesta.destino else None,
        ms=respuesta.ms,
        proveedor=respuesta.proveedor,
    )

    # Volver a dibujar para que los botones del nuevo resultado queden bajo la
    # conversación y la caja de escritura vuelva a estar vacía.
    st.rerun()
