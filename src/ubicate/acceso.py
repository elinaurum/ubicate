"""Puerta de acceso a la aplicación.

**Esto no es autenticación.** Es una clave compartida que decide qué vista se
muestra, mientras no haya cuentas de verdad (ver ADR-0010 y `docs/ROADMAP.md`
§6). No identifica a nadie, no guarda quién entró y no protege datos: sirve
para que la aplicación en construcción no quede abierta a cualquiera que
tropiece con la URL, y para separar la vista estable de la que está en obra.

Vive fuera de ``ui/`` a propósito: así se puede probar sin levantar Streamlit.
"""

from __future__ import annotations

import secrets
from enum import StrEnum

from ubicate.config import Settings


class Rol(StrEnum):
    """Qué versión de la aplicación ve quien entró."""

    USUARIO = "usuario"
    DESARROLLO = "desarrollo"

    @property
    def etiqueta(self) -> str:
        return {
            Rol.USUARIO: "Versión estable",
            Rol.DESARROLLO: "Versión en desarrollo",
        }[self]


def _coincide(candidata: str, esperada: str) -> bool:
    """Comparación en tiempo constante.

    ``compare_digest`` evita que el tiempo de respuesta delate cuántos
    caracteres iniciales acertó quien prueba claves.
    """
    if not esperada:
        return False
    return secrets.compare_digest(candidata.encode("utf-8"), esperada.encode("utf-8"))


def rol_para(clave: str, settings: Settings) -> Rol | None:
    """Rol que abre esta clave, o ``None`` si no abre ninguno.

    Se revisa primero la clave de desarrollo: si alguien configurara las dos
    iguales, conviene que gane la más específica y no la general.
    """
    limpia = (clave or "").strip()
    if not limpia:
        return None
    if _coincide(limpia, settings.clave_desarrollo):
        return Rol.DESARROLLO
    if _coincide(limpia, settings.clave_usuario):
        return Rol.USUARIO
    return None
