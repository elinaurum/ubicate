"""Puerta de acceso (ADR-0010). No es autenticación: ver ubicate/acceso.py."""

import pytest

from ubicate.acceso import Rol, rol_para
from ubicate.config import Settings


@pytest.fixture
def claves() -> Settings:
    return Settings(clave_usuario="user", clave_desarrollo="developer")


def test_la_clave_de_usuario_abre_la_version_estable(claves):
    assert rol_para("user", claves) is Rol.USUARIO


def test_la_clave_de_desarrollo_abre_la_version_en_obra(claves):
    assert rol_para("developer", claves) is Rol.DESARROLLO


@pytest.mark.parametrize("intento", ["", "   ", "otra", "User", "DEVELOPER", "user "])
def test_una_clave_que_no_es_no_abre_nada(claves, intento):
    """Sensible a mayúsculas; los espacios alrededor sí se perdonan."""
    esperado = Rol.USUARIO if intento.strip() == "user" else None
    assert rol_para(intento, claves) is esperado


def test_los_espacios_alrededor_no_estorban(claves):
    """Pegar la clave suele arrastrar un espacio; no debería trancar a nadie."""
    assert rol_para("  developer  ", claves) is Rol.DESARROLLO


def test_una_clave_vacia_en_la_configuracion_no_abre_la_puerta():
    """Si alguien deja una clave sin configurar, esa puerta queda cerrada,
    no abierta a cualquiera."""
    settings = Settings(clave_usuario="", clave_desarrollo="")
    assert rol_para("", settings) is None
    assert rol_para("user", settings) is None


def test_si_las_dos_claves_son_iguales_gana_la_de_desarrollo():
    settings = Settings(clave_usuario="misma", clave_desarrollo="misma")
    assert rol_para("misma", settings) is Rol.DESARROLLO


def test_cada_rol_tiene_una_etiqueta_para_mostrar():
    assert Rol.USUARIO.etiqueta
    assert Rol.DESARROLLO.etiqueta
    assert Rol.USUARIO.etiqueta != Rol.DESARROLLO.etiqueta
