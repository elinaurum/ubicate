"""Vista interior de un piso, separada del mapa exterior (ver ADR-0009).

Reutiliza el patrón del ADR-0004 (folium con ``crs="Simple"``, HTML
autocontenido, imagen incrustada en base64), pero en el sistema de
coordenadas propio del plano de arquitectura de cada piso, en **metros** —
sin relación con el lienzo exterior de ``config.lienzo_alto`` x
``lienzo_ancho``. No se intenta calzar ambos planos (ver limitación M1 y
ADR-0009): esta vista solo responde "cómo es este piso por dentro", no
"dónde cae este piso visto desde arriba".

Igual que ``mapa/render.py``, este módulo no importa Streamlit y devuelve
HTML puro, cacheable.
"""

from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import folium

from ubicate.config import Settings
from ubicate.modelos import Destino, PlantaInterior

COLOR_SALA = "#C0392B"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


@lru_cache(maxsize=16)
def _imagen_data_uri(ruta: str, mtime: float) -> str:
    """Imagen de la planta como data URI. ``mtime`` invalida la caché al cambiar."""
    del mtime
    archivo = Path(ruta)
    datos = base64.b64encode(archivo.read_bytes()).decode("ascii")
    mime = MIME.get(archivo.suffix.lower(), "image/png")
    return f"data:{mime};base64,{datos}"


def imagen_planta_data_uri(settings: Settings, planta: PlantaInterior) -> str:
    archivo = settings.dir_imagenes_plantas / planta.imagen
    if not archivo.exists():
        raise FileNotFoundError(f"no se encuentra la imagen de planta en {archivo}")
    return _imagen_data_uri(str(archivo), archivo.stat().st_mtime)


def _popup_sala(destino: Destino) -> str:
    cuerpo = (
        f"<strong>Sala {html.escape(destino.id)}</strong><br>"
        f"{html.escape(destino.edificio.nombre)} · piso <strong>{destino.piso}</strong>"
    )
    return f"<div style='font-family:system-ui,sans-serif;font-size:13px'>{cuerpo}</div>"


def construir_mapa_interior(
    settings: Settings,
    planta: PlantaInterior,
    salas: list[Destino],
    resaltar_id: str | None = None,
) -> folium.Map:
    bounds = [[0.0, 0.0], [planta.alto_m, planta.ancho_m]]
    centro = [planta.alto_m / 2, planta.ancho_m / 2]

    mapa = folium.Map(location=centro, zoom_start=-1, tiles=None, crs="Simple")
    mapa.options["maxBounds"] = bounds
    mapa.options["maxBoundsViscosity"] = 1.0
    mapa.options["zoomSnap"] = 0.25
    mapa.options["attributionControl"] = False

    folium.raster_layers.ImageOverlay(
        name=f"Piso {planta.piso}",
        image=imagen_planta_data_uri(settings, planta),
        bounds=bounds,
        opacity=1,
        interactive=False,
        cross_origin=False,
        zindex=1,
    ).add_to(mapa)
    mapa.fit_bounds(bounds)

    for destino in salas:
        coord = destino.sala.coord_interior
        radio = 14 if destino.id == resaltar_id else 10
        folium.CircleMarker(
            location=[coord.y, coord.x],
            radius=radio,
            color=COLOR_SALA,
            fill=True,
            fill_opacity=0.92,
            tooltip=destino.etiqueta_corta,
            popup=folium.Popup(_popup_sala(destino), max_width=260),
        ).add_to(mapa)

    return mapa


def mapa_interior_html(
    settings: Settings,
    planta: PlantaInterior,
    salas: list[Destino],
    resaltar_id: str | None = None,
) -> str:
    """HTML autocontenido de la vista interior, listo para incrustar."""
    return construir_mapa_interior(settings, planta, salas, resaltar_id).get_root().render()
