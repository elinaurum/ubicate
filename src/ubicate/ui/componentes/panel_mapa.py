"""Panel del mapa: buscador, desambiguación y plano."""

from __future__ import annotations

import time

import streamlit as st
import streamlit.components.v1 as components

from ubicate.busqueda.buscador import EstadoBusqueda
from ubicate.ui import estado, recursos, tema


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


def _buscador() -> str | None:
    """Campo de destino con sugerencias mientras se escribe.

    Es un ``selectbox`` y no un ``text_input`` porque Streamlit solo filtra
    opciones mientras se teclea en el primero: es la lista desplegable de la
    maqueta. Con ``accept_new_options`` se conserva lo que ya hacía el buscador
    —escribir cualquier cosa y que la resuelva la búsqueda tolerante a erratas—,
    así que se gana el autocompletado sin perder "biblioteka".
    """
    repo = recursos.repositorio()
    etiquetas = {etiqueta: cid for cid, etiqueta in repo.catalogo_mapeable()}

    eleccion = st.selectbox(
        "Ingresa tu destino",
        options=list(etiquetas),
        index=None,
        placeholder="Ingresa tu destino",
        accept_new_options=True,
        label_visibility="collapsed",
        key="ub_input_mapa",
    )
    if eleccion is None:
        return None
    # Si es una opción del catálogo, ya sabemos el id: no hace falta buscar.
    if eleccion in etiquetas:
        estado.fijar_destino(etiquetas[eleccion])
        return None
    return eleccion


def render() -> None:
    repo = recursos.repositorio()

    consulta = _buscador()
    if consulta:
        _resolver_busqueda(consulta)

    # El acceso al chat va arriba, no flotando bajo el mapa como en la maqueta:
    # el plano es alto y ahí el botón queda fuera de pantalla sin desplazarse
    # (ACT-014).
    _acciones()

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
            st.markdown(tema.marca_tarjeta(), unsafe_allow_html=True)
            st.markdown(f"**{destino.etiqueta}**")
            st.caption(f"Partiendo desde {ruta.origen.nombre}")
            st.write(destino.detalle)

    _plano(repo, destino)


def _plano(repo, destino) -> None:
    """El plano que corresponda según la versión (ADR-0010).

    En desarrollo se ve **solo** el plano interior, que es lo que se está
    construyendo; en la estable, solo el mapa del campus. Nunca los dos: tener
    dos mapas encima obliga a preguntarse cuál mira uno.
    """
    alto = recursos.settings().mapa_alto_px

    if estado.modo_desarrollo():
        planta = repo.planta_de(destino) if destino is not None else None
        if planta is None:
            st.info(
                "Versión en desarrollo: acá solo se muestra el plano interior, y por "
                "ahora el único levantado es el piso -1 del edificio 851. Busca una "
                "sala de ese piso (B01 a B09) para verlo."
            )
            return
        resaltar_id = destino.id if destino.sala is not None else None
        components.html(
            recursos.mapa_interior_cacheado(planta.id, resaltar_id),
            height=alto,
            scrolling=False,
        )
        st.caption(
            f"Piso {planta.piso} del edificio 851, en su escala real "
            f"({planta.ancho_m} × {planta.alto_m} m). Pasa el cursor por una sala."
        )
        return

    components.html(
        recursos.mapa_cacheado(estado.destino_id(), estado.origen_id()),
        height=alto,
        scrolling=False,
    )
    st.caption(
        "El plano es una vista cenital: la altura (piso, torre) se indica en el texto. "
        "Ver limitación M1 en la documentación."
    )


def _acciones() -> None:
    """Salidas del mapa: preguntarle al asistente y limpiar lo buscado."""
    assets = recursos.settings().dir_assets
    st.markdown(tema.css_mascota(assets), unsafe_allow_html=True)
    st.markdown(tema.marca_mascota(), unsafe_allow_html=True)
    if st.button(
        "Pregúntame lo que necesites",
        key="ub_abrir_chat",
        use_container_width=True,
        type="primary",
    ):
        estado.fijar_vista(estado.VISTA_CHAT)
        st.rerun()

    if estado.destino_id() and st.button("Limpiar", use_container_width=True):
        estado.limpiar()
        st.rerun()
