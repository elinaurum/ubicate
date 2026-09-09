"""Búsqueda de destinos.

Estrategia en cascada, de mayor a menor certeza:

1. **Exacta** sobre la clave normalizada (id, nombre o alias).
2. **Ambigua** si esa clave apunta a más de un destino → se devuelven todos.
3. **Contiene** si la consulta es subcadena de un nombre indexado.
4. **Difusa** (``difflib``) por encima del umbral configurado.
5. **Vacía** si nada supera el umbral.

Devolver el estado explícitamente (y no ``None``) permite que la interfaz
distinga "no existe" de "sé varias cosas parecidas", que es justamente lo que
el prototipo no hacía.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import StrEnum

from ubicate.busqueda.normalizacion import clave, normalizar
from ubicate.modelos import Destino


class EstadoBusqueda(StrEnum):
    EXACTO = "exacto"
    AMBIGUO = "ambiguo"
    SUGERENCIAS = "sugerencias"
    VACIO = "vacio"


@dataclass(frozen=True, slots=True)
class Resultado:
    estado: EstadoBusqueda
    consulta: str
    destino: Destino | None = None
    candidatos: tuple[Destino, ...] = ()
    puntaje: float = 0.0

    @property
    def encontrado(self) -> bool:
        return self.estado is EstadoBusqueda.EXACTO


@dataclass(frozen=True, slots=True)
class Conflicto:
    """Dos destinos distintos comparten una misma clave de búsqueda."""

    clave: str
    ids: tuple[str, ...]

    def __str__(self) -> str:
        return f"clave {self.clave!r} compartida por {', '.join(self.ids)}"


class Indice:
    """Índice invertido en memoria de clave → destinos."""

    def __init__(self, destinos: dict[str, Destino]) -> None:
        self._destinos = destinos
        self._por_clave: dict[str, list[str]] = {}
        self._nombres: dict[str, str] = {}  # texto normalizado → id destino
        self.conflictos: list[Conflicto] = []
        self._construir()

    def _construir(self) -> None:
        for destino in self._destinos.values():
            textos = [destino.id, destino.nombre]
            if destino.sala is not None:
                textos.extend(destino.sala.aliases)
            else:
                textos.extend(destino.edificio.aliases)

            for texto in textos:
                k = clave(texto)
                if not k:
                    continue
                ids = self._por_clave.setdefault(k, [])
                if destino.id not in ids:
                    ids.append(destino.id)
                self._nombres.setdefault(normalizar(texto), destino.id)

        for k, ids in self._por_clave.items():
            if len(ids) > 1:
                self.conflictos.append(Conflicto(clave=k, ids=tuple(ids)))

    @property
    def claves(self) -> list[str]:
        return list(self._por_clave)

    def buscar(self, consulta: str, *, umbral: float, max_sugerencias: int) -> Resultado:
        bruta = (consulta or "").strip()
        if not bruta:
            return Resultado(EstadoBusqueda.VACIO, consulta=bruta)

        k = clave(bruta)
        if not k:
            return Resultado(EstadoBusqueda.VACIO, consulta=bruta)

        # 1 y 2 — coincidencia exacta
        if k in self._por_clave:
            ids = self._por_clave[k]
            destinos = tuple(self._destinos[i] for i in ids)
            if len(destinos) == 1:
                return Resultado(EstadoBusqueda.EXACTO, bruta, destinos[0], destinos, 1.0)
            return Resultado(EstadoBusqueda.AMBIGUO, bruta, None, destinos, 1.0)

        # 3 — subcadena
        contiene = [
            self._destinos[did]
            for texto, did in self._nombres.items()
            if len(k) >= 3 and k in clave(texto)
        ]
        vistos: dict[str, Destino] = {d.id: d for d in contiene}
        if len(vistos) == 1:
            unico = next(iter(vistos.values()))
            return Resultado(EstadoBusqueda.EXACTO, bruta, unico, (unico,), 0.9)
        if vistos:
            return Resultado(
                EstadoBusqueda.AMBIGUO,
                bruta,
                None,
                tuple(list(vistos.values())[:max_sugerencias]),
                0.9,
            )

        # 4 — difusa
        parecidas = difflib.get_close_matches(
            k, self.claves, n=max_sugerencias, cutoff=umbral
        )
        if parecidas:
            sugeridos: dict[str, Destino] = {}
            for p in parecidas:
                for did in self._por_clave[p]:
                    sugeridos.setdefault(did, self._destinos[did])
            puntaje = difflib.SequenceMatcher(None, k, parecidas[0]).ratio()
            return Resultado(
                EstadoBusqueda.SUGERENCIAS, bruta, None, tuple(sugeridos.values()), puntaje
            )

        return Resultado(EstadoBusqueda.VACIO, consulta=bruta)
