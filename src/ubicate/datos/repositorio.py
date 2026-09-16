"""Repositorio de campus: única puerta de acceso a los datos del plano.

El repositorio se construye una vez por proceso y se comparte entre todas las
sesiones (ver ``ubicate.ui.recursos``). No guarda estado por usuario.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from ubicate.busqueda.buscador import Conflicto, Indice, Resultado
from ubicate.config import Settings
from ubicate.modelos import (
    Acceso,
    Categoria,
    Coordenada,
    Destino,
    Edificio,
    PlantaInterior,
    Ruta,
    Sala,
)

log = logging.getLogger(__name__)

ID_ACCESO = {Acceso.B850: "ACCESO_850", Acceso.B851: "ACCESO_851"}


class ErrorDatos(RuntimeError):
    """Los datos del campus no pudieron cargarse o no son consistentes."""

    def __init__(self, problemas: list[str]) -> None:
        self.problemas = problemas
        super().__init__("Datos del campus inválidos:\n- " + "\n- ".join(problemas))


@dataclass(frozen=True, slots=True)
class Diagnostico:
    """Resumen de salud de los datos, para el panel de administración."""

    edificios: int
    salas: int
    plantas: int
    conflictos: tuple[Conflicto, ...]
    advertencias: tuple[str, ...]


class RepositorioCampus:
    def __init__(
        self,
        edificios: list[Edificio],
        salas: list[Sala],
        plantas: list[PlantaInterior],
        settings: Settings,
    ) -> None:
        self._settings = settings
        self._edificios: dict[str, Edificio] = {e.id: e for e in edificios if e.activo}
        self._salas: dict[str, Sala] = {s.id: s for s in salas if s.activo}
        self._plantas: dict[str, PlantaInterior] = {p.id: p for p in plantas if p.activo}
        self._plantas_por_piso: dict[tuple[Acceso, int], PlantaInterior] = {
            (p.acceso, p.piso): p for p in self._plantas.values()
        }
        self._advertencias: list[str] = []

        self._validar_referencias()
        self._destinos: dict[str, Destino] = self._construir_destinos()
        self._indice = Indice(self._destinos)

        for conflicto in self._indice.conflictos:
            log.warning("conflicto de alias: %s", conflicto)

    # ------------------------------------------------------------------ carga
    @classmethod
    def desde_archivos(cls, settings: Settings) -> RepositorioCampus:
        edificios = _cargar(settings.ruta_edificios, Edificio, "edificio")
        salas = _cargar(settings.ruta_salas, Sala, "sala")
        plantas = _cargar(settings.ruta_plantas, PlantaInterior, "planta")
        return cls(edificios, salas, plantas, settings)

    # ----------------------------------------------------------- validaciones
    def _validar_referencias(self) -> None:
        problemas: list[str] = []

        for acceso, eid in ID_ACCESO.items():
            if eid not in self._edificios:
                problemas.append(f"falta el edificio de acceso {eid} (acceso {acceso.value})")

        for sala in self._salas.values():
            if sala.edificio_id not in self._edificios:
                problemas.append(
                    f"la sala {sala.id} apunta al edificio inexistente {sala.edificio_id}"
                )

        alto, ancho = self._settings.lienzo_alto, self._settings.lienzo_ancho
        for e in self._edificios.values():
            if not (0 <= e.coord.y <= alto and 0 <= e.coord.x <= ancho):
                problemas.append(
                    f"{e.id} tiene coordenada fuera del lienzo "
                    f"({e.coord.y}, {e.coord.x}) para {alto}x{ancho}"
                )

        vistas: set[tuple[Acceso, int]] = set()
        for p in self._plantas.values():
            clave = (p.acceso, p.piso)
            if clave in vistas:
                problemas.append(
                    f"la planta {p.id} repite acceso {p.acceso.value} + piso {p.piso}, "
                    "ya cubierto por otra planta"
                )
            vistas.add(clave)

        for sala in self._salas.values():
            if sala.coord_interior is None:
                continue
            edificio = self._edificios.get(sala.edificio_id)
            if edificio is None:
                continue  # ya se reportó arriba
            planta = self._plantas_por_piso.get((edificio.acceso, sala.piso))
            if planta is None:
                problemas.append(
                    f"la sala {sala.id} tiene coord_interior pero no existe una planta "
                    f"para acceso {edificio.acceso.value} piso {sala.piso}"
                )
                continue
            c = sala.coord_interior
            if not (0 <= c.y <= planta.alto_m and 0 <= c.x <= planta.ancho_m):
                problemas.append(
                    f"la sala {sala.id} tiene coord_interior fuera de la planta {planta.id} "
                    f"({c.y}, {c.x}) para {planta.alto_m}x{planta.ancho_m} m"
                )

        if problemas:
            raise ErrorDatos(problemas)

    def _construir_destinos(self) -> dict[str, Destino]:
        destinos: dict[str, Destino] = {}

        for edificio in self._edificios.values():
            destinos[edificio.id] = Destino(
                id=edificio.id,
                nombre=edificio.nombre,
                categoria=Categoria.EDIFICIO,
                coord=edificio.coord,
                edificio=edificio,
                detalle=edificio.descripcion,
            )

        for sala in self._salas.values():
            edificio = self._edificios[sala.edificio_id]
            if sala.id in destinos:
                self._advertencias.append(
                    f"la sala {sala.id} colisiona con un id de edificio; se conserva la sala"
                )
            destinos[sala.id] = Destino(
                id=sala.id,
                nombre=sala.id,
                categoria=Categoria.SALA,
                coord=edificio.coord,
                edificio=edificio,
                sala=sala,
                detalle=sala.instrucciones,
            )
        return destinos

    # -------------------------------------------------------------- consultas
    def buscar(self, consulta: str) -> Resultado:
        return self._indice.buscar(
            consulta,
            umbral=self._settings.umbral_difuso,
            max_sugerencias=self._settings.max_sugerencias,
        )

    def destino(self, destino_id: str) -> Destino | None:
        return self._destinos.get(destino_id)

    def edificio(self, edificio_id: str) -> Edificio | None:
        return self._edificios.get(edificio_id)

    def accesos(self) -> list[Edificio]:
        return [self._edificios[i] for i in ID_ACCESO.values() if i in self._edificios]

    def origen_para(self, destino: Destino, origen_id: str | None = None) -> Edificio:
        """Punto de partida de la ruta.

        Si el usuario declaró dónde está (``origen_id``) se respeta; si no, se
        usa el acceso del sector al que pertenece el destino. Reemplaza el
        ``id.startswith("851_")`` del prototipo por el campo ``acceso``.
        """
        if origen_id and origen_id in self._edificios:
            return self._edificios[origen_id]
        return self._edificios[ID_ACCESO[destino.acceso]]

    def ruta(self, destino: Destino, origen_id: str | None = None) -> Ruta:
        origen = self.origen_para(destino, origen_id)
        puntos: tuple[Coordenada, ...] = (origen.coord, destino.coord)
        return Ruta(origen=origen, destino=destino, puntos=puntos)

    def salas_de(self, edificio_id: str) -> list[Sala]:
        return sorted(
            (s for s in self._salas.values() if s.edificio_id == edificio_id),
            key=lambda s: (s.piso, s.id),
        )

    def planta_de(self, destino: Destino) -> PlantaInterior | None:
        """Plano interior del piso del destino, si existe (ver ADR-0009).

        None para un edificio (no tiene piso) o para una sala cuyo piso todavía
        no tiene plano levantado.
        """
        if destino.piso is None:
            return None
        return self._plantas_por_piso.get((destino.acceso, destino.piso))

    def salas_en_planta(self, planta: PlantaInterior) -> list[Destino]:
        """Destinos-sala con posición dentro de ``planta``, para dibujarlos."""
        return [
            d
            for d in self._destinos.values()
            if d.sala is not None
            and d.sala.coord_interior is not None
            and d.acceso == planta.acceso
            and d.piso == planta.piso
        ]

    def catalogo_mapeable(self) -> list[tuple[str, str]]:
        """(id, etiqueta) de todo lo localizable. Lo usa el prompt del chat."""
        return sorted(
            ((d.id, d.etiqueta) for d in self._destinos.values()),
            key=lambda par: par[0],
        )

    @property
    def diagnostico(self) -> Diagnostico:
        return Diagnostico(
            edificios=len(self._edificios),
            salas=len(self._salas),
            plantas=len(self._plantas),
            conflictos=tuple(self._indice.conflictos),
            advertencias=tuple(self._advertencias),
        )

    def plantas(self) -> list[PlantaInterior]:
        return list(self._plantas.values())


def _cargar(ruta: Path, modelo, etiqueta: str) -> list:
    if not ruta.exists():
        raise ErrorDatos([f"no existe el archivo de datos {ruta}"])
    try:
        crudo = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErrorDatos([f"{ruta.name} no es JSON válido: {exc}"]) from exc

    if not isinstance(crudo, list):
        raise ErrorDatos([f"{ruta.name} debe contener una lista de objetos"])

    objetos, problemas = [], []
    for i, item in enumerate(crudo):
        try:
            objetos.append(modelo.model_validate(item))
        except ValidationError as exc:
            ident = item.get("id", f"#{i}") if isinstance(item, dict) else f"#{i}"
            for error in exc.errors():
                campo = ".".join(str(p) for p in error["loc"]) or "(raíz)"
                problemas.append(f"{etiqueta} {ident}: {campo} — {error['msg']}")

    vistos: set[str] = set()
    for obj in objetos:
        if obj.id in vistos:
            problemas.append(f"{etiqueta} {obj.id}: id duplicado")
        vistos.add(obj.id)

    if problemas:
        raise ErrorDatos(problemas)
    return objetos
