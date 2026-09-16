"""Vista interior de un piso, separada del mapa exterior (ver ADR-0009).

Se dibuja **como vector**: cada sala es una forma con su color y su etiqueta,
y cada referencia (baño, ascensor, piscina…) es un símbolo. No se incrusta el
dibujo del plano de arquitectura como imagen: ese dibujo está lleno de detalle
de construcción (cotas, ductos, pilotes) que estorba a quien solo quiere
ubicarse.

Todo está en el sistema de coordenadas propio del piso, en **metros**, tal
como sale del plano (ver ``scripts/extraer_planta_dxf.py``). No tiene relación
con el lienzo del mapa exterior.

Igual que ``mapa/render.py``, este módulo no importa Streamlit y devuelve HTML
puro, cacheable (ADR-0004).
"""

from __future__ import annotations

import html

import folium

from ubicate.config import Settings
from ubicate.modelos import Destino, PlantaInterior, PuntoInteres, TipoPunto

COLOR_SALA = "#C0392B"
COLOR_SALA_RELLENO = "#E8B5AE"
COLOR_SALA_ACTIVA = "#8E1B0F"
COLOR_PISO = "#EDEFF2"
COLOR_BORDE_PISO = "#C6CBD4"
COLOR_TEXTO = "#2C3E50"

# Símbolo y color por tipo de referencia. El símbolo es un carácter: no
# necesita archivos de iconos ni una fuente externa que cargar.
SIMBOLOS: dict[TipoPunto, tuple[str, str]] = {
    TipoPunto.BANO: ("🚻", "#2E86C1"),
    TipoPunto.PISCINA: ("🏊", "#17A589"),
    TipoPunto.CAMARIN: ("🚿", "#17A589"),
    TipoPunto.ASCENSOR: ("🛗", "#7D3C98"),
    TipoPunto.ESCALERA: ("🪜", "#7D3C98"),
}


def _etiqueta_html(texto: str, color: str, tamano: int = 13) -> folium.DivIcon:
    seguro = html.escape(texto)
    return folium.DivIcon(
        html=(
            f"<div style=\"font-family:system-ui,sans-serif;font-size:{tamano}px;"
            f"font-weight:600;color:{color};white-space:nowrap;"
            'text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;'
            f'transform:translate(-50%,-50%)">{seguro}</div>'
        ),
        icon_size=(0, 0),
    )


def _simbolo_html(simbolo: str, color: str) -> folium.DivIcon:
    return folium.DivIcon(
        html=(
            '<div style="transform:translate(-50%,-50%);display:flex;'
            "align-items:center;justify-content:center;width:26px;height:26px;"
            f"border-radius:50%;background:{color};border:2px solid #fff;"
            'box-shadow:0 1px 3px rgba(0,0,0,.35);font-size:14px;line-height:1">'
            f"{simbolo}</div>"
        ),
        icon_size=(0, 0),
    )


def _tooltip(texto: str) -> folium.Tooltip:
    """Tooltip con el texto escapado.

    folium inserta el tooltip tal cual en el HTML: sin escapar, un rótulo del
    plano con ``<script>`` se ejecutaría en el navegador. Ver CLAUDE.md §5
    ("escapa siempre lo que venga de datos").
    """
    return folium.Tooltip(html.escape(texto))


def _popup(titulo: str, detalle: str = "") -> folium.Popup:
    cuerpo = f"<strong>{html.escape(titulo)}</strong>"
    if detalle:
        cuerpo += f"<br>{html.escape(detalle)}"
    return folium.Popup(
        f"<div style='font-family:system-ui,sans-serif;font-size:13px'>{cuerpo}</div>",
        max_width=260,
    )


def _dibujar_sala(destino: Destino, activa: bool, capa: folium.FeatureGroup) -> None:
    sala = destino.sala
    color = COLOR_SALA_ACTIVA if activa else COLOR_SALA
    detalle = f"{destino.edificio.nombre} · piso {destino.piso}"

    if sala.poligono_interior:
        folium.Polygon(
            locations=[c.como_lista() for c in sala.poligono_interior],
            color=color,
            weight=2 if not activa else 3,
            fill=True,
            fill_color=COLOR_SALA_RELLENO,
            fill_opacity=0.95 if activa else 0.8,
            tooltip=_tooltip(destino.etiqueta_corta),
            popup=_popup(f"Sala {destino.id}", detalle),
        ).add_to(capa)
    else:
        # Sin contorno derivable del plano: se marca el punto, no se inventa
        # una forma. Ver docs/DEUDA_DATOS.md D-06.
        folium.CircleMarker(
            location=sala.coord_interior.como_lista(),
            radius=13,
            color=color,
            weight=2,
            fill=True,
            fill_color=COLOR_SALA_RELLENO,
            fill_opacity=0.9,
            tooltip=_tooltip(destino.etiqueta_corta),
            popup=_popup(f"Sala {destino.id}", detalle),
        ).add_to(capa)

    folium.Marker(
        location=sala.coord_interior.como_lista(),
        icon=_etiqueta_html(destino.id, COLOR_SALA_ACTIVA if activa else COLOR_TEXTO),
    ).add_to(capa)


def _dibujar_punto(punto: PuntoInteres, capa: folium.FeatureGroup) -> None:
    simbolo, color = SIMBOLOS.get(punto.tipo, ("•", COLOR_TEXTO))
    folium.Marker(
        location=punto.coord.como_lista(),
        icon=_simbolo_html(simbolo, color),
        tooltip=_tooltip(punto.nombre),
        popup=_popup(punto.nombre),
    ).add_to(capa)


def construir_mapa_interior(
    settings: Settings,
    planta: PlantaInterior,
    salas: list[Destino],
    resaltar_id: str | None = None,
) -> folium.Map:
    del settings  # la vista interior no depende de la configuración del lienzo exterior
    bounds = [[0.0, 0.0], [planta.alto_m, planta.ancho_m]]

    mapa = folium.Map(
        location=[planta.alto_m / 2, planta.ancho_m / 2],
        zoom_start=-1,
        tiles=None,
        crs="Simple",
        zoom_control=True,
    )
    mapa.options["maxBounds"] = [[-10, -10], [planta.alto_m + 10, planta.ancho_m + 10]]
    mapa.options["maxBoundsViscosity"] = 1.0
    mapa.options["zoomSnap"] = 0.25
    mapa.options["attributionControl"] = False

    # Superficie del piso: es la caja de los muros del plano, no la silueta
    # exacta del edificio. Sirve de fondo neutro para ubicar lo demás.
    folium.Rectangle(
        bounds=bounds,
        color=COLOR_BORDE_PISO,
        weight=1,
        fill=True,
        fill_color=COLOR_PISO,
        fill_opacity=1,
        interactive=False,
    ).add_to(mapa)

    capa = folium.FeatureGroup(name=f"Piso {planta.piso}")
    for destino in salas:
        if destino.sala is None or destino.sala.coord_interior is None:
            continue
        _dibujar_sala(destino, destino.id == resaltar_id, capa)
    for punto in planta.puntos:
        _dibujar_punto(punto, capa)
    capa.add_to(mapa)

    mapa.fit_bounds(bounds)
    return mapa


def mapa_interior_html(
    settings: Settings,
    planta: PlantaInterior,
    salas: list[Destino],
    resaltar_id: str | None = None,
) -> str:
    """HTML autocontenido de la vista interior, listo para incrustar."""
    return construir_mapa_interior(settings, planta, salas, resaltar_id).get_root().render()
