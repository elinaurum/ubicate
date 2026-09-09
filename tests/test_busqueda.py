from ubicate.busqueda.buscador import EstadoBusqueda


def test_busqueda_exacta_por_id(repo):
    r = repo.buscar("B04")
    assert r.estado is EstadoBusqueda.EXACTO
    assert r.destino.id == "B04"


def test_busqueda_tolerante_a_formato(repo):
    for consulta in ("b-04", "sala B 04", "  B04  "):
        assert repo.buscar(consulta).destino.id == "B04"


def test_busqueda_por_nombre_de_edificio(repo):
    assert repo.buscar("física").destino.id == "850_FIS"


def test_ambiguedad_devuelve_candidatos(repo):
    r = repo.buscar("auditorio")
    assert r.estado is EstadoBusqueda.AMBIGUO
    assert {c.id for c in r.candidatos} == {"850_AUDITORIO", "851_AUDITORIO"}


def test_error_de_tipeo_devuelve_sugerencias(repo):
    r = repo.buscar("biblioteka")
    assert r.estado is EstadoBusqueda.SUGERENCIAS
    assert "850_BIBLIOTECA" in {c.id for c in r.candidatos}


def test_consulta_desconocida_es_vacia(repo):
    assert repo.buscar("zzzqqq999").estado is EstadoBusqueda.VACIO


def test_consulta_vacia_no_revienta(repo):
    assert repo.buscar("   ").estado is EstadoBusqueda.VACIO
