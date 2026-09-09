def test_base_no_vacia(kb):
    assert len(kb.fragmentos) > 50
    assert kb.documentos


def test_recuperacion_pertinente(kb):
    resultados = kb.buscar("paletas de ping pong", k=3)
    assert resultados
    assert "ping pong" in resultados[0].fragmento.texto.lower()


def test_consulta_sin_terminos_utiles(kb):
    assert kb.buscar("¿?", k=3) == []


def test_fragmentos_tienen_fuente(kb):
    for f in kb.fragmentos[:20]:
        assert f.documento.fuente
        assert f.cita
