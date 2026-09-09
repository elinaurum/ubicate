"""Selección y configuración de proveedores."""

import types

import pytest

from ubicate.chat.proveedores import (
    ErrorProveedor,
    Mensaje,
    ProveedorEco,
    ProveedorOpenAI,
    config_pensamiento,
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
    """Devuelve siempre la misma respuesta: sirve para los casos que fallan."""
    prov = ProveedorOpenAI(Settings(proveedor_llm="gemini", api_key="x"))
    monkeypatch.setattr(
        prov._cliente.chat.completions,
        "create",
        lambda **_: _respuesta_falsa(contenido, finish_reason),
    )
    return prov


def _proveedor_secuencia(monkeypatch, *respuestas):
    """Devuelve una respuesta distinta por llamada: sirve para el reintento."""
    prov = ProveedorOpenAI(Settings(proveedor_llm="gemini", api_key="x"))
    salidas = iter([_respuesta_falsa(c, r) for c, r in respuestas])
    monkeypatch.setattr(
        prov._cliente.chat.completions, "create", lambda **_: next(salidas)
    )
    return prov


# --- Completitud de la respuesta -----------------------------------------


def test_respuesta_normal_se_devuelve(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "  Hola.  ", "stop")
    assert prov.responder("s", [Mensaje("user", "hola")]) == "Hola."


def test_corte_por_tokens_se_reintenta_y_se_recupera(monkeypatch):
    prov = _proveedor_secuencia(
        monkeypatch,
        ("Puedes usar los microondas disponibles en el Casino Domey", "length"),
        ("Hay microondas en el Casino Domey.", "stop"),
    )
    assert prov.responder("s", [Mensaje("user", "dónde almuerzo")]) == (
        "Hay microondas en el Casino Domey."
    )


def test_corte_por_tokens_persistente_explica_la_causa(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "Puedes usar los microondas del", "length")
    with pytest.raises(ErrorProveedor, match="UBICATE_MAX_TOKENS"):
        prov.responder("s", [Mensaje("user", "dónde almuerzo")])


def test_razon_desconocida_tambien_cuenta_como_corte(monkeypatch):
    # Gemini vía endpoint compatible no reporta "recitation" con ese nombre.
    prov = _proveedor_openai(monkeypatch, "Biblioteca de 850 y la", "other")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "dónde estudio")])


def test_recitation_de_gemini_es_error(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "Biblioteca de 850 y la", "recitation")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "dónde estudio")])


def test_texto_sin_cierre_es_corte_aunque_diga_stop(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "Puedes usar los microondas del", "stop")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "dónde almuerzo")])


def test_marca_de_lugar_es_cierre_valido(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "Está en el piso -1.\n[[LUGAR:B04]]", "stop")
    assert "[[LUGAR:B04]]" in prov.responder("s", [Mensaje("user", "B04")])


def test_respuesta_vacia_es_error(monkeypatch):
    prov = _proveedor_openai(monkeypatch, "", "stop")
    with pytest.raises(ErrorProveedor):
        prov.responder("s", [Mensaje("user", "hola")])


# --- Configuración de pensamiento ----------------------------------------


def test_pensamiento_solo_se_envia_a_gemini():
    gemini = config_pensamiento(Settings(proveedor_llm="gemini", api_key="x"))
    assert gemini == {
        "extra_body": {"google": {"thinking_config": {"thinking_level": "minimal"}}}
    }
    assert config_pensamiento(Settings(proveedor_llm="groq", api_key="x")) is None


def test_pensamiento_numerico_usa_presupuesto():
    settings = Settings(proveedor_llm="gemini", api_key="x", nivel_pensamiento="0")
    assert config_pensamiento(settings) == {
        "extra_body": {"google": {"thinking_config": {"thinking_budget": 0}}}
    }


def test_pensamiento_auto_no_envia_nada():
    settings = Settings(proveedor_llm="gemini", api_key="x", nivel_pensamiento="auto")
    assert config_pensamiento(settings) is None


def test_modelo_que_rechaza_el_pensamiento_sigue_funcionando(monkeypatch):
    prov = ProveedorOpenAI(Settings(proveedor_llm="gemini", api_key="x"))
    llamadas = []

    def create(**kwargs):
        llamadas.append(kwargs)
        if "extra_body" in kwargs:
            raise RuntimeError("400 INVALID_ARGUMENT: unknown field thinking_config")
        return _respuesta_falsa("Está en el piso -1.", "stop")

    monkeypatch.setattr(prov._cliente.chat.completions, "create", create)
    assert prov.responder("s", [Mensaje("user", "B04")]) == "Está en el piso -1."
    assert len(llamadas) == 2
    assert prov._pensamiento is None


# --- Selección de proveedor ----------------------------------------------


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