"""Construcción del mapa del campus sobre el plano de Beauchef.

Decisiones relevantes (ver docs/decisiones/ADR-0004):

* La imagen del plano se incrusta como **data URI en base64**. Una ruta
  relativa (``assets/mapa_beauchef.png``) no resuelve dentro del iframe donde
  el navegador monta el mapa, que era la causa del plano en blanco.
* El módulo devuelve **HTML puro**. No importa Streamlit, de modo que se puede
  probar sin levantar la aplicación y el resultado se puede cachear.
"""

from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import folium

from ubicate.config import Settings
from ubicate.modelos import Categoria, Destino, Ruta

COLOR_SALA = "#C0392B"
COLOR_EDIFICIO = "#1F6FB2"
COLOR_ORIGEN = "#1E8449"
COLOR_RUTA = "#34495E"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


@lru_cache(maxsize=4)
def _plano_data_uri(ruta: str, mtime: float) -> str:
    """Imagen del plano como data URI. ``mtime`` invalida la caché al cambiar."""
    del mtime
    archivo = Path(ruta)
    datos = base64.b64encode(archivo.read_bytes()).decode("ascii")
    mime = MIME.get(archivo.suffix.lower(), "image/png")
    return f"data:{mime};base64,{datos}"


def plano_data_uri(settings: Settings) -> str:
    archivo = settings.ruta_imagen_mapa
    if not archivo.exists():
        raise FileNotFoundError(f"no se encuentra el plano del campus en {archivo}")
    return _plano_data_uri(str(archivo), archivo.stat().st_mtime)


def _envolver(texto: str, palabras_por_linea: int = 6) -> str:
    """Corta el texto en líneas para que el globo no se desborde a lo ancho."""
    palabras = html.escape(texto or "").split()
    lineas = [
        " ".join(palabras[i : i + palabras_por_linea])
        for i in range(0, len(palabras), palabras_por_linea)
    ]
    return "<br>".join(lineas)


def _popup_destino(destino: Destino) -> str:
    if destino.categoria is Categoria.SALA:
        cuerpo = (
            f"<strong>Sala {html.escape(destino.id)}</strong><br>"
            f"{html.escape(destino.edificio.nombre)} · piso <strong>{destino.piso}</strong>"
            "<hr style='margin:4px 0'>"
            f"{_envolver(destino.detalle)}"
        )
    else:
        cuerpo = (
            f"<strong>{html.escape(destino.nombre)}</strong>"
            "<hr style='margin:4px 0'>"
            f"{_envolver(destino.detalle, 8)}"
        )
    return f"<div style='font-family:system-ui,sans-serif;font-size:13px'>{cuerpo}</div>"


def construir_mapa(
    settings: Settings,
    destino: Destino | None = None,
    ruta: Ruta | None = None,
) -> folium.Map:
    limites = settings.limites_lienzo
    centro = [settings.lienzo_alto / 2, settings.lienzo_ancho / 2]

    mapa = folium.Map(location=centro, zoom_start=-1, tiles=None, crs="Simple")
    mapa.options["maxBounds"] = limites
    mapa.options["maxBoundsViscosity"] = 1.0
    mapa.options["minZoom"] = -2
    mapa.options["zoomSnap"] = 0.25
    mapa.options["attributionControl"] = False

    folium.raster_layers.ImageOverlay(
        name="Plano Beauchef",
        image=plano_data_uri(settings),
        bounds=limites,
        opacity=1,
        interactive=False,
        cross_origin=False,
        zindex=1,
    ).add_to(mapa)

    mapa.fit_bounds(limites)

    if destino is None:
        return mapa

    capa = folium.FeatureGroup(name="Ruta y destino")
    color = COLOR_SALA if destino.categoria is Categoria.SALA else COLOR_EDIFICIO

    if ruta is not None:
        folium.PolyLine(
            locations=ruta.como_listas(),
            color=COLOR_RUTA,
            weight=5,
            opacity=0.85,
            dash_array="8, 6",
        ).add_to(capa)

        folium.CircleMarker(
            location=ruta.origen.coord.como_lista(),
            radius=11,
            color=COLOR_ORIGEN,
            fill=True,
            fill_opacity=1,
            tooltip=f"Partida: {ruta.origen.nombre}",
            popup=folium.Popup(f"<b>Partida</b><br>{html.escape(ruta.origen.nombre)}", max_width=260),
        ).add_to(capa)

    folium.CircleMarker(
        location=destino.coord.como_lista(),
        radius=16,
        color=color,
        fill=True,
        fill_opacity=0.92,
        tooltip=destino.etiqueta,
        popup=folium.Popup(_popup_destino(destino), max_width=320),
    ).add_to(capa)

    capa.add_to(mapa)

    if ruta is not None:
        mapa.fit_bounds(ruta.bounds, padding=(60, 60))
    return mapa


def mapa_html(
    settings: Settings,
    destino: Destino | None = None,
    ruta: Ruta | None = None,
) -> str:
    """HTML autocontenido del mapa, listo para incrustar."""
    return construir_mapa(settings, destino, ruta).get_root().render()
