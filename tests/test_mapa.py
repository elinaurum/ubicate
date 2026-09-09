from ubicate.mapa.render import mapa_html


def test_mapa_base_incluye_el_plano_embebido(settings):
    html = mapa_html(settings)
    assert "data:image/png;base64" in html


def test_mapa_con_destino_dibuja_marcador_y_ruta(settings, repo):
    destino = repo.destino("B04")
    html = mapa_html(settings, destino, repo.ruta(destino))
    assert "Sala B04" in html
    assert "polyline" in html.lower()


def test_popup_escapa_contenido_de_los_datos(settings, repo):
    """Una descripción maliciosa en el JSON no debe inyectarse como HTML."""
    import dataclasses

    original = repo.destino("850_FIS")
    sucio = dataclasses.replace(original, detalle="<script>alert(1)</script>")
    html = mapa_html(settings, sucio, None)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
