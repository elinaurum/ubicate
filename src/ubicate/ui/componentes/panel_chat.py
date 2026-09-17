"""Panel de conversación."""

from __future__ import annotations

import streamlit as st

from ubicate.chat.motor import Conversacion
from ubicate.chat.prompts import SALUDO
from ubicate.ui import estado, recursos, tema

AVATAR_USUARIO = "🧑‍🎓"


def _avatar(rol: str) -> str:
    """El asistente usa la mascota; si no está el archivo, un emoji."""
    if rol == "user":
        return AVATAR_USUARIO
    return tema.avatar_asistente(recursos.settings().dir_assets)


def _marca_de_rol(rol: str) -> None:
    """Deja una marca invisible para que el CSS pueda pintar cada burbuja.

    Esta versión de Streamlit no distingue en el HTML un mensaje del asistente
    de uno de quien pregunta, y sus clases `st-emotion-cache-…` cambian con
    cada versión. La marca propia es estable (ver ui/tema.py).
    """
    st.markdown(f'<span class="ub-rol-{rol}"></span>', unsafe_allow_html=True)


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
    if st.button("← Volver al mapa", key="ub_volver_mapa"):
        estado.fijar_vista(estado.VISTA_MAPA)
        st.rerun()

    conversacion = estado.conversacion()

    contenedor = st.container(height=460, border=True)
    with contenedor:
        st.markdown(tema.marca_tarjeta(), unsafe_allow_html=True)
        if not conversacion.mensajes:
            with st.chat_message("assistant", avatar=_avatar("assistant")):
                _marca_de_rol("assistant")
                st.markdown(SALUDO)
        for mensaje in conversacion.mensajes:
            with st.chat_message(mensaje.rol, avatar=_avatar(mensaje.rol)):
                _marca_de_rol(mensaje.rol)
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
        with st.chat_message("user", avatar=_avatar("user")):
            _marca_de_rol("user")
            st.markdown(consulta)
        with st.chat_message("assistant", avatar=_avatar("assistant")):
            _marca_de_rol("assistant")
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
