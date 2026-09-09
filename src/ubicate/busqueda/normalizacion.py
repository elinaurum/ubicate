"""Normalización de texto para búsqueda tolerante a errores.

Objetivo: que "B-04", "b 04", "sala B04" y "B04" caigan todos en la misma
clave. Esto elimina la necesidad de enumerar a mano cada variante ortográfica
como alias en los JSON, que es lo que hacía la versión anterior.
"""

from __future__ import annotations

import re
import unicodedata

# Palabras que el usuario escribe pero no aportan a la identificación del lugar.
VACIAS = frozenset(
    {
        "la", "el", "los", "las", "de", "del", "en", "al", "a", "un", "una",
        "sala", "salas", "salon", "edificio", "auditorio_de", "donde", "queda",
        "esta", "está", "ubicada", "ubicado", "ir", "llegar", "hacia", "por",
        "favor", "me", "puedes", "mostrar", "buscar", "busca", "quiero",
    }
)

_SEPARADORES = re.compile(r"[\-_/.,;:()\[\]'\"“”‘’]+")
_NO_ALFANUM = re.compile(r"[^a-z0-9 ]+")
_ESPACIOS = re.compile(r"\s+")


def sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin puntuación y sin palabras vacías."""
    t = sin_tildes(str(texto)).lower()
    t = _SEPARADORES.sub(" ", t)
    t = _NO_ALFANUM.sub(" ", t)
    t = _ESPACIOS.sub(" ", t).strip()
    if not t:
        return ""
    tokens = [p for p in t.split(" ") if p not in VACIAS]
    return " ".join(tokens) if tokens else t


def clave(texto: str) -> str:
    """Clave canónica de indexación: normalizada y sin espacios.

    >>> clave("B-04") == clave("b 04") == clave("sala B04")
    True
    """
    return normalizar(texto).replace(" ", "")


def tokens(texto: str) -> list[str]:
    n = normalizar(texto)
    return n.split(" ") if n else []
