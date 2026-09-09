def test_base_no_vacia(kb):
    assert len(kb.fragmentos) > 50
    assert kb.documentos


def test_recuperacion_pertinente(kb):
    resultados = kb.buscar("paletas de ping pong", k=3)
    assert resultados
    assert "ping pong" in resultados[0].fragmento.texto.lower()


def test_consulta_sin_terminos_utiles(kb):
    assert kb.buscar("¿?", k=3) == []


def test_pregunta_natural_no_arrastra_fragmentos_irrelevantes(kb):
    """"dónde puedo ir a estudiar" no debe recuperar el fragmento de ping pong
    solo porque su título empieza con "¿Dónde puedo…?"."""
    resultados = kb.buscar("dónde puedo ir a estudiar", k=6)
    assert resultados
    assert "estudiar" in resultados[0].fragmento.titulo.lower()
    assert all("ping pong" not in r.fragmento.texto.lower() for r in resultados)


def test_palabras_de_pregunta_no_cuentan_como_termino(kb):
    # Solo palabras vacías / de pregunta: no hay término con el que puntuar.
    assert kb.buscar("qué puedo ver aquí", k=3) == []


def test_fragmentos_tienen_fuente(kb):
    for f in kb.fragmentos[:20]:
        assert f.documento.fuente
        assert f.cita
