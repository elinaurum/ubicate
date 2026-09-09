"""Recursos compartidos entre sesiones.

Clave para escalar: ``@st.cache_resource`` construye el repositorio, la base de
conocimiento y el motor **una sola vez por proceso**, no una vez por usuario.
Con 2.000 personas la diferencia es entre cargar 300 fragmentos una vez o
300 × 2.000 veces.

Ninguno de estos objetos guarda estado por usuario: el historial de
conversación vive en el estado de sesión (``ui.estado``).
"""

from __future__ import annotations

import streamlit as st

from ubicate.chat.conocimiento import BaseConocimiento
from ubicate.chat.motor import MotorChat
from ubicate.chat.proveedores import crear_proveedor
from ubicate.config import Settings, get_settings
from ubicate.datos.repositorio import RepositorioCampus
from ubicate.mapa.render import mapa_html
from ubicate.modelos import Destino, Ruta
from ubicate.observabilidad.metricas import RegistroConsultas
from ubicate.observabilidad.registro import configurar


@st.cache_resource(show_spinner=False)
def settings() -> Settings:
    s = get_settings()
    configurar(s)
    return s


@st.cache_resource(show_spinner="Cargando el plano del campus…")
def repositorio() -> RepositorioCampus:
    return RepositorioCampus.desde_archivos(settings())


@st.cache_resource(show_spinner="Cargando la base de conocimiento…")
def conocimiento() -> BaseConocimiento:
    return BaseConocimiento.desde_directorio(settings().dir_kb)


@st.cache_resource(show_spinner=False)
def motor() -> MotorChat:
    s = settings()
    return MotorChat(s, repositorio(), conocimiento(), crear_proveedor(s))


@st.cache_resource(show_spinner=False)
def registro() -> RegistroConsultas:
    return RegistroConsultas(settings())


@st.cache_data(show_spinner=False, ttl=3600, max_entries=512)
def mapa_cacheado(destino_id: str | None, origen_id: str | None) -> str:
    """HTML del mapa, memorizado por combinación destino×origen.

    El plano en base64 pesa ~120 KB: regenerarlo en cada interacción de cada
    usuario es el principal costo evitable de la vista.
    """
    s = settings()
    if destino_id is None:
        return mapa_html(s)

    repo = repositorio()
    destino: Destino | None = repo.destino(destino_id)
    if destino is None:
        return mapa_html(s)
    ruta: Ruta = repo.ruta(destino, origen_id)
    return mapa_html(s, destino, ruta)
