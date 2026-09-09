"""Estado de sesión tipado y límites de uso.

Centralizar las claves del ``session_state`` evita el problema clásico de
Streamlit: strings mágicos repartidos por toda la aplicación que nadie sabe
quién escribe ni cuándo.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

import streamlit as st

from ubicate.chat.motor import Conversacion
from ubicate.config import Settings


class Claves:
    SESION = "ub_sesion"
    CONVERSACION = "ub_conversacion"
    DESTINO = "ub_destino_id"
    ORIGEN = "ub_origen_id"
    CANDIDATOS = "ub_candidatos"
    ULTIMO_MENSAJE = "ub_ultimo_mensaje_ts"
    CONTADOR = "ub_contador_mensajes"
    VISTA = "ub_vista"


# Vistas de la interfaz. En un teléfono no caben el chat y el mapa a la vez, así
# que se muestra una sola y se navega entre ellas (ver ACT-004).
VISTA_CHAT = "chat"
VISTA_MAPA = "mapa"


@dataclass(frozen=True, slots=True)
class Veredicto:
    permitido: bool
    motivo: str = ""


def inicializar() -> None:
    st.session_state.setdefault(Claves.SESION, secrets.token_hex(8))
    st.session_state.setdefault(Claves.CONVERSACION, Conversacion())
    st.session_state.setdefault(Claves.DESTINO, None)
    st.session_state.setdefault(Claves.ORIGEN, None)
    st.session_state.setdefault(Claves.CANDIDATOS, [])
    st.session_state.setdefault(Claves.ULTIMO_MENSAJE, 0.0)
    st.session_state.setdefault(Claves.CONTADOR, 0)
    st.session_state.setdefault(Claves.VISTA, VISTA_CHAT)


def id_sesion() -> str:
    return st.session_state[Claves.SESION]


def conversacion() -> Conversacion:
    return st.session_state[Claves.CONVERSACION]


def destino_id() -> str | None:
    return st.session_state[Claves.DESTINO]


def origen_id() -> str | None:
    return st.session_state[Claves.ORIGEN]


def vista() -> str:
    return st.session_state[Claves.VISTA]


def fijar_vista(valor: str) -> None:
    st.session_state[Claves.VISTA] = valor


def fijar_destino(valor: str | None) -> None:
    st.session_state[Claves.DESTINO] = valor
    st.session_state[Claves.CANDIDATOS] = []


def fijar_origen(valor: str | None) -> None:
    st.session_state[Claves.ORIGEN] = valor


def candidatos() -> list:
    return st.session_state[Claves.CANDIDATOS]


def fijar_candidatos(valores: list) -> None:
    st.session_state[Claves.CANDIDATOS] = valores


def limpiar() -> None:
    st.session_state[Claves.DESTINO] = None
    st.session_state[Claves.CANDIDATOS] = []


def limpiar_conversacion() -> None:
    st.session_state[Claves.CONVERSACION] = Conversacion()
    st.session_state[Claves.CONTADOR] = 0


def permitir_mensaje(settings: Settings) -> Veredicto:
    """Cortafuegos de costo y abuso, por sesión."""
    ahora = time.monotonic()
    if st.session_state[Claves.CONTADOR] >= settings.mensajes_por_sesion:
        return Veredicto(
            False,
            "Alcanzaste el límite de mensajes de esta sesión. "
            "Puedes seguir usando el buscador del mapa o recargar la página.",
        )
    espera = settings.segundos_entre_mensajes - (ahora - st.session_state[Claves.ULTIMO_MENSAJE])
    if espera > 0:
        return Veredicto(False, "Espera un segundo antes de enviar otro mensaje.")
    return Veredicto(True)


def registrar_envio() -> None:
    st.session_state[Claves.ULTIMO_MENSAJE] = time.monotonic()
    st.session_state[Claves.CONTADOR] += 1
