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
    # Posición dentro del plano interior del piso (PlantaInterior), en metros,
    # con el mismo origen abajo-izquierda que Coordenada. None mientras no se
    # levante el dato (ver docs/DATOS.md §6 y ROADMAP §7). No tiene relación con
    # el lienzo exterior: cada piso usa su propio sistema, tal como sale del
    # plano de arquitectura.
    coord_interior: Coordenada | None = None
    # Contorno de la sala en ese mismo sistema. Solo se carga cuando se pudo
    # derivar del plano con certeza (ver scripts/extraer_planta_dxf.py): si la
    # sala no es rectangular, queda en None y se dibuja como punto, en vez de
    # inventarle una forma aproximada.
    poligono_interior: tuple[Coordenada, ...] | None = None

    @field_validator("poligono_interior")
    @classmethod
    def _poligono_suficiente(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError("poligono_interior necesita al menos 3 vértices")
        return v

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


class TipoPunto(StrEnum):
    """Categorías de punto de referencia dentro de un piso."""

    BANO = "bano"
    PISCINA = "piscina"
    CAMARIN = "camarin"
    ASCENSOR = "ascensor"
    ESCALERA = "escalera"


class PuntoInteres(BaseModel):
    """Referencia dentro de un piso (baño, ascensor, piscina…).

    El nombre es el rótulo textual del plano de arquitectura, no uno
    inventado: si el plano dice "VESTIBULO BAÑO ALUMNAS 1", eso se guarda.

    ``poligono`` es el recinto que ocupa, cuando el plano lo encierra como un
    espacio propio. Queda en None para lo que no tiene recinto —un hall de
    ascensores está dentro de la circulación, una escalera está trazada con
    sus peldaños— y en ese caso se dibuja solo el símbolo. No se le inventa
    una forma (regla 3.1).
    """

    model_config = ConfigDict(frozen=True)

    nombre: str = Field(min_length=2)
    tipo: TipoPunto
    coord: Coordenada
    poligono: tuple[Coordenada, ...] | None = None

    @field_validator("poligono")
    @classmethod
    def _poligono_suficiente(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError("poligono necesita al menos 3 vértices")
        return v


class PlantaInterior(BaseModel):
    """Plano interior de un piso, con su propio sistema de coordenadas.

    Es la vista exclusiva del piso (ver ADR-0009), separada del mapa exterior:
    ``ancho_m``/``alto_m`` son el tamaño real del piso en metros, tal como se
    extrajo del plano de arquitectura (``scripts/extraer_planta_dxf.py``), y
    tanto ``Sala.coord_interior`` como ``PuntoInteres.coord`` están expresadas
    en ese mismo sistema. No se intenta calzar con el lienzo del mapa exterior.

    Se dibuja como vector (formas y símbolos), no como imagen del plano CAD.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    acceso: Acceso
    piso: int
    ancho_m: float = Field(gt=0)
    alto_m: float = Field(gt=0)
    # Archivo GeoJSON en assets/plantas/ con los recintos del piso (pasillos,
    # halls, servicios: todo lo que no es una sala del catálogo). Se genera con
    # scripts/extraer_planta_dxf.py --recintos y no se edita a mano.
    geometria: str = ""
    puntos: tuple[PuntoInteres, ...] = ()
    fuente: str = ""
    activo: bool = True

    @field_validator("id")
    @classmethod
    def _id_valido(cls, v: str) -> str:
        if not RE_ID.match(v):
            raise ValueError(f"id de planta inválido: {v!r} (usa MAYÚSCULAS_Y_GUION_BAJO)")
        return v


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
