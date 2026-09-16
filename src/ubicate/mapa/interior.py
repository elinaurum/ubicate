"""Vista interior de un piso, separada del mapa exterior (ver ADR-0009).

El piso se dibuja **completo y como vector**: cada recinto —sala, pasillo,
hall, baño, sala de máquinas— es una figura con su borde y su relleno, con la
forma que tiene en el plano de arquitectura. Todo en gris; lo que es un
destino se pone verde al pasar el cursor por encima.

Los recintos se reconstruyen a partir de los muros del plano
(``scripts/extraer_planta_dxf.py --recintos``) y viven en un GeoJSON dentro de
``assets/plantas/``. Las coordenadas están en **metros**, en el sistema propio
del piso, sin relación con el lienzo del mapa exterior.

Igual que ``mapa/render.py``, este módulo no importa Streamlit y devuelve HTML
puro, cacheable (ADR-0004).
"""

from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

import folium

from ubicate.config import Settings
from ubicate.modelos import Destino, PlantaInterior, PuntoInteres, TipoPunto

# Todo el piso es gris; el verde queda reservado para "el cursor está aquí".
GRIS_FONDO = "#F4F5F7"
GRIS_RECINTO = "#DCDFE4"
GRIS_BORDE = "#9AA1AC"
GRIS_DESTINO = "#C9CED6"
GRIS_BORDE_DESTINO = "#6B7280"
GRIS_TEXTO = "#374151"
BLANCO = "#FFFFFF"
VERDE = "#1E8449"
VERDE_RELLENO = "#A9DFBF"

# Símbolo por tipo de referencia: un carácter, sin archivos ni fuentes externas.
SIMBOLOS: dict[TipoPunto, str] = {
    TipoPunto.BANO: "🚻",
    TipoPunto.PISCINA: "🏊",
    TipoPunto.CAMARIN: "🚿",
    TipoPunto.ASCENSOR: "🛗",
    TipoPunto.ESCALERA: "🪜",
}


@lru_cache(maxsize=16)
def _geometria(ruta: str, mtime: float) -> dict:
    """Recintos del piso. ``mtime`` invalida la caché al cambiar el archivo."""
    del mtime
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def geometria_de(settings: Settings, planta: PlantaInterior) -> dict:
    """GeoJSON con los recintos del piso; vacío si la planta no tiene."""
    if not planta.geometria:
        return {"type": "FeatureCollection", "features": []}
    archivo = settings.dir_plantas / planta.geometria
    if not archivo.exists():
        raise FileNotFoundError(f"no se encuentra la geometría de la planta en {archivo}")
    return _geometria(str(archivo), archivo.stat().st_mtime)


def _estilo_recinto(_feature) -> dict:
    return {
        "color": GRIS_BORDE,
        "weight": 1,
        "fillColor": GRIS_RECINTO,
        "fillOpacity": 1,
    }


def _estilo_destino(_feature) -> dict:
    return {
        "color": GRIS_BORDE_DESTINO,
        "weight": 2,
        "fillColor": GRIS_DESTINO,
        "fillOpacity": 1,
    }


def _estilo_cursor(_feature) -> dict:
    """Retroalimentación: el cursor está sobre este destino."""
    return {
        "color": VERDE,
        "weight": 3,
        "fillColor": VERDE_RELLENO,
        "fillOpacity": 1,
    }


def _etiqueta(texto: str, color: str = GRIS_TEXTO, tamano: int = 12) -> folium.DivIcon:
    seguro = html.escape(texto)
    return folium.DivIcon(
        html=(
            f'<div style="font:700 {tamano}px system-ui,sans-serif;color:{color};'
            "white-space:nowrap;pointer-events:none;transform:translate(-50%,-50%);"
            'text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff,0 0 3px #fff">'
            f"{seguro}</div>"
        ),
        icon_size=(0, 0),
    )


def _simbolo(caracter: str) -> folium.DivIcon:
    return folium.DivIcon(
        html=(
            '<div style="font-size:11px;line-height:1;pointer-events:none;'
            f'transform:translate(-50%,-50%)">{caracter}</div>'
        ),
        icon_size=(0, 0),
    )


def _feature_sala(destino: Destino) -> dict:
    """Feature GeoJSON de una sala. GeoJSON usa [x, y]; el modelo, [y, x].

    El nombre se escapa aquí: ``GeoJsonTooltip`` termina insertando el valor
    con ``innerHTML``, así que un rótulo con ``<img onerror=…>`` se ejecutaría
    (ver ACT-011). Escapado, se muestra igual y no se ejecuta.
    """
    sala = destino.sala
    propiedades = {"nombre": html.escape(f"Sala {destino.id}"), "id": destino.id}
    if sala.poligono_interior:
        anillo = [[c.x, c.y] for c in sala.poligono_interior]
        anillo.append(anillo[0])
        geometria = {"type": "Polygon", "coordinates": [anillo]}
    else:
        # Sin contorno derivable del plano: punto, no una forma inventada.
        geometria = {
            "type": "Point",
            "coordinates": [sala.coord_interior.x, sala.coord_interior.y],
        }
    return {"type": "Feature", "properties": propiedades, "geometry": geometria}


def _feature_punto(punto: PuntoInteres) -> dict:
    """Feature GeoJSON de una referencia. El nombre se escapa: ver ``_feature_sala``.

    Con recinto propio en el plano se dibuja su forma; sin él, un punto.
    """
    if punto.poligono:
        anillo = [[c.x, c.y] for c in punto.poligono]
        anillo.append(anillo[0])
        geometria = {"type": "Polygon", "coordinates": [anillo]}
    else:
        geometria = {"type": "Point", "coordinates": [punto.coord.x, punto.coord.y]}
    return {
        "type": "Feature",
        "properties": {"nombre": html.escape(punto.nombre)},
        "geometry": geometria,
    }


def _tooltip(campos: list[str]) -> folium.GeoJsonTooltip:
    return folium.GeoJsonTooltip(fields=campos, labels=False, sticky=True)


def construir_mapa_interior(
    settings: Settings,
    planta: PlantaInterior,
    salas: list[Destino],
    resaltar_id: str | None = None,
) -> folium.Map:
    bounds = [[0.0, 0.0], [planta.alto_m, planta.ancho_m]]

    mapa = folium.Map(
        location=[planta.alto_m / 2, planta.ancho_m / 2],
        zoom_start=0,
        tiles=None,
        crs="Simple",
        zoom_control=True,
    )
    mapa.options["maxBounds"] = [[-10, -10], [planta.alto_m + 10, planta.ancho_m + 10]]
    mapa.options["maxBoundsViscosity"] = 1.0
    mapa.options["zoomSnap"] = 0.25
    mapa.options["attributionControl"] = False

    folium.Rectangle(
        bounds=bounds,
        color=GRIS_FONDO,
        weight=1,
        fill=True,
        fill_color=GRIS_FONDO,
        fill_opacity=1,
        interactive=False,
    ).add_to(mapa)

    # 1. El piso completo: pasillos, halls, servicios, salas de máquinas.
    folium.GeoJson(
        geometria_de(settings, planta),
        style_function=_estilo_recinto,
        interactive=False,
        name="Recintos",
    ).add_to(mapa)

    # 2. Los destinos: salas del catálogo. Verde bajo el cursor.
    dibujables = [d for d in salas if d.sala is not None and d.sala.coord_interior is not None]
    con_forma = [d for d in dibujables if d.sala.poligono_interior]
    sin_forma = [d for d in dibujables if not d.sala.poligono_interior]

    if con_forma:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": [_feature_sala(d) for d in con_forma]},
            style_function=_estilo_destino,
            highlight_function=_estilo_cursor,
            tooltip=_tooltip(["nombre"]),
            name="Salas",
        ).add_to(mapa)

    if sin_forma:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": [_feature_sala(d) for d in sin_forma]},
            marker=folium.CircleMarker(
                radius=11, color=GRIS_BORDE_DESTINO, weight=2, fill=True,
                fill_color=GRIS_DESTINO, fill_opacity=1,
            ),
            style_function=_estilo_destino,
            highlight_function=_estilo_cursor,
            tooltip=_tooltip(["nombre"]),
            name="Salas sin contorno",
        ).add_to(mapa)

    # 3. Referencias del piso: baños, piscina, camarines, ascensores, escaleras.
    #    Con recinto propio se dibujan como figura; el resto, como símbolo.
    con_recinto = [p for p in planta.puntos if p.poligono]
    sin_recinto = [p for p in planta.puntos if not p.poligono]

    if con_recinto:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": [_feature_punto(p) for p in con_recinto]},
            style_function=_estilo_destino,
            highlight_function=_estilo_cursor,
            tooltip=_tooltip(["nombre"]),
            name="Referencias",
        ).add_to(mapa)

    if sin_recinto:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": [_feature_punto(p) for p in sin_recinto]},
            marker=folium.CircleMarker(
                radius=9, color=GRIS_BORDE_DESTINO, weight=2, fill=True,
                fill_color=BLANCO, fill_opacity=1,
            ),
            style_function=lambda f: {
                "color": GRIS_BORDE_DESTINO, "weight": 2,
                "fillColor": BLANCO, "fillOpacity": 1,
            },
            highlight_function=_estilo_cursor,
            tooltip=_tooltip(["nombre"]),
            name="Referencias sin recinto",
        ).add_to(mapa)

    for punto in planta.puntos:
        folium.Marker(
            location=punto.coord.como_lista(),
            icon=_simbolo(SIMBOLOS.get(punto.tipo, "•")),
        ).add_to(mapa)

    # 4. Etiquetas encima de todo.
    for destino in dibujables:
        folium.Marker(
            location=destino.sala.coord_interior.como_lista(),
            icon=_etiqueta(
                destino.id,
                VERDE if destino.id == resaltar_id else GRIS_TEXTO,
                13 if destino.id == resaltar_id else 12,
            ),
        ).add_to(mapa)

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
