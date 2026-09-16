"""Vista interior de un piso (ver ADR-0009)."""

from ubicate.mapa.interior import mapa_interior_html


def test_mapa_interior_incluye_el_plano_embebido(settings, repo):
    destino = repo.destino("B01")
    planta = repo.planta_de(destino)
    salas = repo.salas_en_planta(planta)
    html = mapa_interior_html(settings, planta, salas)
    assert "data:image/png;base64" in html


def test_mapa_interior_dibuja_las_salas_de_la_planta(settings, repo):
    destino = repo.destino("B01")
    planta = repo.planta_de(destino)
    salas = repo.salas_en_planta(planta)
    html = mapa_interior_html(settings, planta, salas)
    assert "Sala B01" in html
    assert "Sala B08" in html


def test_mapa_interior_sin_salas_no_falla(settings, repo):
    destino = repo.destino("B01")
    planta = repo.planta_de(destino)
    html = mapa_interior_html(settings, planta, [])
    assert "data:image/png;base64" in html
