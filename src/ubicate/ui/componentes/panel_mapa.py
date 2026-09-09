"""Panel del mapa: buscador, desambiguación y plano."""

from __future__ import annotations

import time

import streamlit as st
import streamlit.components.v1 as components

from ubicate.busqueda.buscador import EstadoBusqueda
from ubicate.ui import estado, recursos


def _resolver_busqueda(consulta: str) -> None:
    repo = recursos.repositorio()
    inicio = time.perf_counter()
    resultado = repo.buscar(consulta)
    ms = int((time.perf_counter() - inicio) * 1000)

    recursos.registro().registrar(
        sesion=estado.id_sesion(),
        origen="buscador",
        consulta=consulta,
        estado=resultado.estado.value,
        destino_id=resultado.destino.id if resultado.destino else None,
        ms=ms,
    )

    if resultado.estado is EstadoBusqueda.EXACTO and resultado.destino:
        estado.fijar_destino(resultado.destino.id)
    elif resultado.estado in (EstadoBusqueda.AMBIGUO, EstadoBusqueda.SUGERENCIAS):
        estado.fijar_candidatos(list(resultado.candidatos))
        st.session_state["ub_estado_busqueda"] = resultado.estado.value
    else:
        estado.fijar_candidatos([])
        st.session_state["ub_estado_busqueda"] = EstadoBusqueda.VACIO.value


def _selector_origen() -> None:
    """Punto de partida de la ruta: el respaldo manual mientras no haya
    geolocalización (sección 9.3 de la documentación)."""
    repo = recursos.repositorio()
    accesos = repo.accesos()
    etiquetas = ["Detectar según el destino"] + [a.nombre for a in accesos]

    indice = 0
    for i, acceso in enumerate(accesos, start=1):
        if acceso.id == estado.origen_id():
            indice = i

    with st.expander(f"Punto de partida: {etiquetas[indice]}"):
        eleccion = st.selectbox(
            "¿Desde dónde partes?",
            etiquetas,
            index=indice,
            label_visibility="collapsed",
        )
    estado.fijar_origen(
        None if eleccion == etiquetas[0] else accesos[etiquetas.index(eleccion) - 1].id
    )


def render() -> None:
    repo = recursos.repositorio()
    st.subheader("Mapa del campus")

    col_busqueda, col_limpiar = st.columns([5, 1])
    with col_busqueda:
        consulta = st.text_input(
            "Buscar sala o edificio",
            placeholder="B04, Física, Auditorio Gorbea, biblioteca…",
            label_visibility="collapsed",
            key="ub_input_mapa",
        )
    with col_limpiar:
        if st.button("Limpiar", use_container_width=True):
            estado.limpiar()
            st.rerun()

    if consulta:
        _resolver_busqueda(consulta)

    _selector_origen()

    # --- Desambiguación ---------------------------------------------------
    opciones = estado.candidatos()
    if opciones:
        etiqueta = (
            "Encontré varias coincidencias, ¿cuál buscas?"
            if st.session_state.get("ub_estado_busqueda") == EstadoBusqueda.AMBIGUO.value
            else "No encontré eso exactamente. ¿Quisiste decir…?"
        )
        st.info(etiqueta)
        for candidato in opciones:
            if st.button(candidato.etiqueta, key=f"cand_{candidato.id}", use_container_width=True):
                estado.fijar_destino(candidato.id)
                st.rerun()
    elif st.session_state.get("ub_estado_busqueda") == EstadoBusqueda.VACIO.value and consulta:
        st.warning(
            f"No tengo «{consulta}» en el plano. Si crees que debería estar, avísanos: "
            "queda registrado para agregarlo."
        )

    # --- Ficha del destino -------------------------------------------------
    destino = repo.destino(estado.destino_id()) if estado.destino_id() else None
    if destino is not None:
        ruta = repo.ruta(destino, estado.origen_id())
        with st.container(border=True):
            st.markdown(f"**{destino.etiqueta}**")
            st.caption(f"Partiendo desde {ruta.origen.nombre}")
            st.write(destino.detalle)

    # --- Plano -------------------------------------------------------------
    html = recursos.mapa_cacheado(estado.destino_id(), estado.origen_id())
    components.html(html, height=recursos.settings().mapa_alto_px, scrolling=False)
    st.caption(
        "El plano es una vista cenital: la altura (piso, torre) se indica en el texto. "
        "Ver limitación M1 en la documentación."
    )
