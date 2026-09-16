"""Integridad de los datos reales del campus. Corre en CI ante cada cambio."""

from ubicate.modelos import Acceso, Categoria


def test_carga_sin_errores(repo):
    d = repo.diagnostico
    assert d.edificios > 0 and d.salas > 0


def test_sin_conflictos_de_alias(repo):
    conflictos = repo.diagnostico.conflictos
    assert not conflictos, "alias ambiguos: " + "; ".join(str(c) for c in conflictos)


def test_toda_sala_apunta_a_un_edificio_existente(repo):
    for cid, _ in repo.catalogo_mapeable():
        destino = repo.destino(cid)
        if destino.categoria is Categoria.SALA:
            assert repo.edificio(destino.sala.edificio_id) is not None


def test_accesos_presentes(repo):
    ids = {a.id for a in repo.accesos()}
    assert ids == {"ACCESO_850", "ACCESO_851"}


def test_coordenadas_dentro_del_lienzo(repo, settings):
    for cid, _ in repo.catalogo_mapeable():
        c = repo.destino(cid).coord
        assert 0 <= c.y <= settings.lienzo_alto
        assert 0 <= c.x <= settings.lienzo_ancho


def test_origen_de_ruta_por_sector(repo):
    b04 = repo.destino("B04")            # sector 851
    fis = repo.destino("850_FIS")        # sector 850
    assert b04.acceso is Acceso.B851
    assert repo.origen_para(b04).id == "ACCESO_851"
    assert repo.origen_para(fis).id == "ACCESO_850"


def test_origen_manual_tiene_prioridad(repo):
    b04 = repo.destino("B04")
    assert repo.origen_para(b04, "ACCESO_850").id == "ACCESO_850"


def test_sala_con_coord_interior_tiene_planta_valida(repo):
    """Ver ADR-0009: toda coord_interior debe caer dentro de su planta."""
    b01 = repo.destino("B01")
    planta = repo.planta_de(b01)
    assert planta is not None
    assert planta.piso == -1
    c = b01.sala.coord_interior
    assert c is not None
    assert 0 <= c.y <= planta.alto_m
    assert 0 <= c.x <= planta.ancho_m


def test_la_planta_tiene_tamano_de_edificio_real(repo):
    """Guardia contra el error de escala del DXF (ACT-010): el piso -1 del 851
    mide ~100 x 70 m. Si alguien recarga el plano tomando los milímetros que
    declara su encabezado, el marco queda 10 veces más chico y esto lo caza."""
    planta = repo.planta_de(repo.destino("B01"))
    assert 50 <= planta.ancho_m <= 300
    assert 30 <= planta.alto_m <= 300


def test_las_salas_rectangulares_miden_lo_que_una_sala(repo):
    """Una sala de clases con contorno debe tener un área creíble (20-200 m²)."""
    for cid in ("B01", "B02", "B03", "B04"):
        sala = repo.destino(cid).sala
        assert sala.poligono_interior, f"{cid} debería tener contorno"
        pts = [(c.x, c.y) for c in sala.poligono_interior]
        n = len(pts)
        area = abs(
            sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                for i in range(n))
        ) / 2
        assert 20 <= area <= 200, f"{cid} tiene {area:.1f} m2"


def test_los_puntos_de_referencia_estan_dentro_de_la_planta(repo):
    planta = repo.planta_de(repo.destino("B01"))
    assert planta.puntos, "la planta debería traer referencias (baños, ascensores…)"
    tipos = {p.tipo.value for p in planta.puntos}
    assert {"bano", "piscina", "ascensor", "escalera"} <= tipos
    for p in planta.puntos:
        assert 0 <= p.coord.y <= planta.alto_m
        assert 0 <= p.coord.x <= planta.ancho_m


def test_edificio_no_tiene_planta_interior(repo):
    assert repo.planta_de(repo.destino("850_FIS")) is None


def test_sala_sin_planta_levantada_no_falla(repo):
    """F21 (piso 2, sector 850) no tiene plano interior todavía: debe dar None,
    no reventar."""
    assert repo.planta_de(repo.destino("F21")) is None


def test_salas_en_planta_incluye_las_confirmadas(repo):
    planta = repo.planta_de(repo.destino("B01"))
    ids = {d.id for d in repo.salas_en_planta(planta)}
    assert ids == {"B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09"}


def test_las_referencias_con_recinto_tienen_forma(repo):
    """Baños, camarines y piscina se dibujan como figura; los halls de
    ascensor y la mayoría de las escaleras no tienen recinto propio en el
    plano y quedan como símbolo (ver ACT-011)."""
    planta = repo.planta_de(repo.destino("B01"))
    con_forma = [p for p in planta.puntos if p.poligono]
    assert len(con_forma) >= 12
    nombres = {p.nombre for p in con_forma}
    assert "PISCINA" in nombres
    assert "CAMARIN HOMBRES" in nombres
    assert any(n.startswith("VESTIBULO BAÑO") for n in nombres)
    for p in con_forma:
        for c in p.poligono:
            assert 0 <= c.y <= planta.alto_m
            assert 0 <= c.x <= planta.ancho_m
