"""Vista interior de un piso, dibujada como vector (ver ADR-0009)."""

from ubicate.mapa.interior import mapa_interior_html


def _planta_y_salas(repo):
    destino = repo.destino("B01")
    planta = repo.planta_de(destino)
    return planta, repo.salas_en_planta(planta)


def test_dibuja_las_salas_de_la_planta(settings, repo):
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "Sala B01" in html
    assert "Sala B08" in html


def test_la_sala_con_contorno_se_dibuja_como_poligono(settings, repo):
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "L.polygon" in html


def test_no_incrusta_el_plano_cad_como_imagen(settings, repo):
    """El rediseño dejó de usar la imagen del DXF: si vuelve, es una regresión."""
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "data:image/png;base64" not in html


def test_incluye_las_referencias_del_piso(settings, repo):
    planta, salas = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, salas)
    assert "PISCINA" in html
    assert "CAMARIN HOMBRES" in html


def test_escapa_el_contenido_de_los_datos(settings, repo):
    """Un rótulo malicioso en el JSON no debe inyectarse como HTML."""
    import dataclasses

    from ubicate.modelos import PuntoInteres, TipoPunto

    planta, salas = _planta_y_salas(repo)
    sucia = planta.model_copy(
        update={
            "puntos": (
                PuntoInteres(
                    nombre="<script>alert(1)</script>",
                    tipo=TipoPunto.BANO,
                    coord=planta.puntos[0].coord,
                ),
            )
        }
    )
    del dataclasses
    html = mapa_interior_html(settings, sucia, salas)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_sin_salas_no_falla(settings, repo):
    planta, _ = _planta_y_salas(repo)
    html = mapa_interior_html(settings, planta, [])
    assert "L.rectangle" in html
