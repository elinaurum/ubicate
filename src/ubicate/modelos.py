"""Modelos de dominio de U-bícate.

Son la única definición autorizada de la forma de los datos. Los archivos JSON
de ``data/`` se validan contra estos modelos al cargarse: si un dato está mal,
la aplicación falla en el arranque y no en producción frente al usuario.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RE_ID = re.compile(r"^[A-Z0-9_]{2,40}$")


class Acceso(StrEnum):
    """Portería por la que se entra al sector donde está el destino."""

    B850 = "850"
    B851 = "851"


class TipoLugar(StrEnum):
    EDIFICIO = "edificio"
    ACCESO = "acceso"
    SERVICIO = "servicio"
    DEPORTIVO = "deportivo"
    ESPACIO_ABIERTO = "espacio_abierto"


class TipoSala(StrEnum):
    CLASE = "clase"
    AUDITORIO = "auditorio"
    LABORATORIO = "laboratorio"
    ESTUDIO = "estudio"


class Coordenada(BaseModel):
    """Punto sobre el lienzo del plano, en orden (y, x) como espera folium."""

    model_config = ConfigDict(frozen=True)

    y: float = Field(ge=0)
    x: float = Field(ge=0)

    @model_validator(mode="before")
    @classmethod
    def _desde_lista(cls, valor):
        if isinstance(valor, (list, tuple)):
            if len(valor) != 2:
                raise ValueError("coord debe tener exactamente dos elementos [y, x]")
            return {"y": valor[0], "x": valor[1]}
        return valor

    def como_lista(self) -> list[float]:
        return [self.y, self.x]


class Edificio(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=False)

    id: str
    nombre: str = Field(min_length=2)
    tipo: TipoLugar = TipoLugar.EDIFICIO
    acceso: Acceso
    coord: Coordenada
    aliases: tuple[str, ...] = ()
    descripcion: str = ""
    activo: bool = True

    @field_validator("id")
    @classmethod
    def _id_valido(cls, v: str) -> str:
        if not RE_ID.match(v):
            raise ValueError(f"id de edificio inválido: {v!r} (usa MAYÚSCULAS_Y_GUION_BAJO)")
        return v

    @field_validator("aliases")
    @classmethod
    def _aliases_limpios(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(a.strip() for a in v if a and a.strip()))

    @property
    def es_acceso(self) -> bool:
        return self.tipo is TipoLugar.ACCESO


class Sala(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=False)

    id: str
    edificio_id: str
    piso: int
    tipo: TipoSala = TipoSala.CLASE
    aliases: tuple[str, ...] = ()
    instrucciones: str = Field(min_length=5)
    activo: bool = True

    @field_validator("id", "edificio_id")
    @classmethod
    def _id_valido(cls, v: str) -> str:
        if not RE_ID.match(v):
            raise ValueError(f"id inválido: {v!r}")
        return v

    @field_validator("piso", mode="before")
    @classmethod
    def _piso_entero(cls, v):
        if isinstance(v, str):
            v = v.strip().replace("−", "-")  # el guion largo aparece en los datos originales
            if v.upper() in {"N/A", "", "-"}:
                raise ValueError("piso no puede quedar vacío")
        return int(v)

    @field_validator("aliases")
    @classmethod
    def _aliases_limpios(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(a.strip() for a in v if a and a.strip()))


class Categoria(StrEnum):
    SALA = "sala"
    EDIFICIO = "edificio"


@dataclass(frozen=True, slots=True)
class Destino:
    """Vista unificada de "algo a lo que se puede llegar".

    El buscador, el mapa y el chat trabajan sobre ``Destino`` y no sobre
    ``Sala``/``Edificio`` por separado: así la lógica de ruteo y de dibujo se
    escribe una sola vez.
    """

    id: str
    nombre: str
    categoria: Categoria
    coord: Coordenada
    edificio: Edificio
    sala: Sala | None = None
    detalle: str = ""

    @property
    def piso(self) -> int | None:
        return self.sala.piso if self.sala else None

    @property
    def acceso(self) -> Acceso:
        return self.edificio.acceso

    @property
    def etiqueta(self) -> str:
        if self.categoria is Categoria.SALA:
            return f"Sala {self.id} — {self.edificio.nombre} (piso {self.piso})"
        return self.edificio.nombre

    @property
    def etiqueta_corta(self) -> str:
        """Nombre breve para un botón o una lista."""
        if self.categoria is Categoria.SALA:
            return f"Sala {self.id}"
        return self.nombre


@dataclass(frozen=True, slots=True)
class Ruta:
    """Trazado simple origen → destino sobre el plano."""

    origen: Edificio
    destino: Destino
    puntos: tuple[Coordenada, ...] = field(default=())

    @property
    def bounds(self) -> list[list[float]]:
        ys = [p.y for p in self.puntos]
        xs = [p.x for p in self.puntos]
        return [[min(ys), min(xs)], [max(ys), max(xs)]]

    def como_listas(self) -> list[list[float]]:
        return [p.como_lista() for p in self.puntos]
