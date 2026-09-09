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
