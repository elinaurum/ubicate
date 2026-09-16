"""Vista interior de un piso: el piso completo dibujado como vector (ADR-0009)."""

from ubicate.mapa.interior import geometria_de, mapa_interior_html


def _planta_y_salas(repo):
    destino = repo.destino("B01")
    planta = repo.planta_de(destino)
    return planta, repo.salas_en_planta(planta)


def test_dibuja_las_salas_de_la_planta(settings, repo):
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "Sala B01" in html
    assert "Sala B08" in html


def test_dibuja_el_piso_completo_no_solo_las_salas(settings, repo):
    """El piso se modela entero: los recintos comunes (pasillos, halls,
    servicios) también se dibujan, no solo las 8 salas del catálogo."""
    planta, salas = _planta_y_salas(repo)
    recintos = geometria_de(settings, planta)
    assert len(recintos["features"]) > 100, "faltan los recintos del piso"
    html = mapa_interior_html(settings, planta, salas)
    assert html.count('"type": "Polygon"') > 100


def test_todas_las_salas_tienen_contorno(settings, repo):
    """Incluidas las hexagonales: se reconstruyen desde los muros."""
    planta, salas = _planta_y_salas(repo)
    del planta
    for destino in salas:
        assert destino.sala.poligono_interior, f"{destino.id} sin contorno"


def test_no_incrusta_el_plano_cad_como_imagen(settings, repo):
    """El piso es vector: si vuelve una imagen del DXF, es una regresión."""
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "data:image/png;base64" not in html


def test_resalta_en_verde_bajo_el_cursor(settings, repo):
    """El único verde de la vista es la retroalimentación del cursor."""
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "#1E8449" in html  # borde verde
    assert "#A9DFBF" in html  # relleno verde


def test_incluye_las_referencias_del_piso(settings, repo):
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "PISCINA" in html
    assert "CAMARIN HOMBRES" in html


def test_las_referencias_con_recinto_se_dibujan_como_figura(settings, repo):
    """La piscina, los camarines y los baños son figuras, no solo un símbolo."""
    planta, salas = _planta_y_salas(repo)
    piscina = next(p for p in planta.puntos if p.nombre == "PISCINA")
    assert piscina.poligono, "la piscina debería tener recinto"
    html = mapa_interior_html(settings, planta, salas)
    # su primer vértice tiene que aparecer dibujado
    assert str(piscina.poligono[0].x) in html


def test_escapa_el_contenido_de_los_datos(settings, repo):
    """``GeoJsonTooltip`` inserta el valor con ``innerHTML``: un rótulo con
    ``<img onerror=…>`` se ejecutaría si no se escapa (ACT-011)."""
    from ubicate.modelos import PuntoInteres, TipoPunto

    planta, salas = _planta_y_salas(repo)
    sucia = planta.model_copy(
        update={
            "puntos": (
                PuntoInteres(
                    nombre="<img src=x onerror=alert(1)>",
                    tipo=TipoPunto.BANO,
                    coord=planta.puntos[0].coord,
                ),
            )
        }
    )
    html = mapa_interior_html(settings, sucia, salas)
    # Lo peligroso es que llegue una etiqueta abierta; escapada es solo texto.
    assert "<img" not in html
    assert "lt;img" in html, "el rótulo debería llegar escapado, no desaparecer"


def test_sin_salas_no_falla(settings, repo):
    planta, _ = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, [])
    assert "L.rectangle" in html
