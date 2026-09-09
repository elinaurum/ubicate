"""Selección y configuración de proveedores."""

import types

import pytest

from ubicate.chat.proveedores import (
    ErrorProveedor,
    Mensaje,
    ProveedorEco,
    ProveedorOpenAI,
    crear_proveedor,
)
from ubicate.config import Settings


def _respuesta_falsa(contenido, finish_reason):
    eleccion = types.SimpleNamespace(
        message=types.SimpleNamespace(content=contenido),
        finish_reason=finish_reason,
    )
    return types.SimpleNamespace(choices=[eleccion])


def _proveedor_openai(monkeypatch, contenido, finish_reason):
    prov = ProveedorOpenAI(Settings(proveedor_llm="gemini", api_key="x"))
    monkeypatch.setattr(
        prov._cliente.chat.completions,
        "create",
        lambda **_: _respuesta_falsa(contenido, finish_reason),
    )
    return prov


def test_respuesta_normal_se_devuelve(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "  Hola.  ", "stop")
    assert prov.responder("s", [Mensaje("user", "hola")]) == "Hola."


def test_recitation_de_gemini_es_error(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "Biblioteca de 850 y la", "recitation")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "dónde estudio")])


def test_respuesta_vacia_es_error(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "", "stop")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "hola")])


def test_sin_api_key_cae_a_eco():
    proveedor = crear_proveedor(Settings(proveedor_llm="gemini", api_key=None))
    assert isinstance(proveedor, ProveedorEco)


def test_eco_es_el_valor_por_defecto():
    assert isinstance(crear_proveedor(Settings()), ProveedorEco)


def test_gemini_y_groq_traen_su_endpoint():
    gemini = Settings(proveedor_llm="gemini", api_key="x")
    groq = Settings(proveedor_llm="groq", api_key="x")
    assert "generativelanguage.googleapis.com" in gemini.base_url_efectiva
    assert "api.groq.com" in groq.base_url_efectiva
    assert gemini.usa_llm and groq.usa_llm


def test_compatible_exige_base_url():
    sin_url = Settings(proveedor_llm="compatible", api_key="x")
    con_url = Settings(proveedor_llm="compatible", api_key="x", base_url="http://local/v1")
    assert not sin_url.usa_llm
    assert con_url.usa_llm
    # Sin URL debe degradar a eco en vez de reventar.
    assert isinstance(crear_proveedor(sin_url), ProveedorEco)


def test_base_url_explicita_gana():
    s = Settings(proveedor_llm="gemini", api_key="x", base_url="http://proxy.local/v1")
    assert s.base_url_efectiva == "http://proxy.local/v1"


def test_reintenta_ante_limite_de_velocidad():
    from ubicate.chat.proveedores import con_reintento

    llamadas = {"n": 0}

    def falla_una_vez():
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            raise RuntimeError("429 rate limit exceeded")
        return "ok"

    assert con_reintento(falla_una_vez, intentos=3, espera_base=0.0) == "ok"
    assert llamadas["n"] == 2


def test_no_reintenta_ante_error_permanente():
    from ubicate.chat.proveedores import con_reintento

    llamadas = {"n": 0}

    def modelo_inexistente():
        llamadas["n"] += 1
        raise RuntimeError("404 model not found")

    import contextlib

    with contextlib.suppress(RuntimeError):
        con_reintento(modelo_inexistente, intentos=3, espera_base=0.0)
    assert llamadas["n"] == 1, "un modelo inexistente no se arregla esperando"
