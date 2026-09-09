"""Orquestación del chat.

Flujo por consulta:

    consulta → recuperación BM25 → prompt (sistema + historial) → proveedor
             → extracción de la marca [[LUGAR:ID]] → destino para el mapa

La extracción de la marca es lo que cierra el Objetivo 3 de la documentación
original: la respuesta del chatbot enciende el marcador en el mapa sin que el
usuario tenga que copiar el nombre al buscador.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

from ubicate.chat.conocimiento import BaseConocimiento, FragmentoPuntuado
from ubicate.chat.prompts import VERSION_PROMPT, construir_sistema
from ubicate.chat.proveedores import ErrorProveedor, Mensaje, Proveedor, ProveedorEco
from ubicate.config import Settings
from ubicate.datos.repositorio import RepositorioCampus
from ubicate.modelos import Destino

log = logging.getLogger(__name__)

RE_LUGAR = re.compile(r"\[\[\s*LUGAR\s*:\s*([A-Z0-9_]+)\s*\]\]", re.IGNORECASE)
FRASES_SIN_RESPUESTA = (
    "no tengo", "no encontré", "no encuentro", "no cuento con",
    "no aparece", "no dispongo", "no está en mi base",
)


@dataclass(frozen=True, slots=True)
class Respuesta:
    texto: str
    destino: Destino | None = None
    fragmentos: tuple[FragmentoPuntuado, ...] = ()
    sin_respuesta: bool = False
    proveedor: str = "eco"
    ms: int = 0
    error: str | None = None

    @property
    def citas(self) -> list[str]:
        vistas: list[str] = []
        for f in self.fragmentos:
            if f.fragmento.cita not in vistas:
                vistas.append(f.fragmento.cita)
        return vistas


@dataclass
class Conversacion:
    """Historial de una sesión. Vive en el estado de sesión, no en el motor."""

    mensajes: list[Mensaje] = field(default_factory=list)

    def agregar(self, rol: str, texto: str) -> None:
        self.mensajes.append(Mensaje(rol=rol, texto=texto))

    def recientes(self, max_turnos: int) -> list[Mensaje]:
        return self.mensajes[-(max_turnos * 2) :]


class MotorChat:
    def __init__(
        self,
        settings: Settings,
        repositorio: RepositorioCampus,
        conocimiento: BaseConocimiento,
        proveedor: Proveedor,
    ) -> None:
        self._settings = settings
        self._repo = repositorio
        self._kb = conocimiento
        self._proveedor = proveedor
        self._catalogo = repositorio.catalogo_mapeable()

    @property
    def proveedor(self) -> str:
        return self._proveedor.nombre

    @property
    def version_prompt(self) -> str:
        return VERSION_PROMPT

    def responder(self, consulta: str, conversacion: Conversacion) -> Respuesta:
        inicio = time.perf_counter()
        consulta = (consulta or "").strip()
        if not consulta:
            return Respuesta(texto="¿Qué necesitas encontrar?", proveedor=self.proveedor)

        recuperados = self._kb.buscar(consulta, k=self._settings.kb_fragmentos)

        # Una coincidencia exacta con una sala o edificio se agrega al contexto:
        # el mapa y el chat comparten la misma verdad sobre el campus.
        resultado_espacial = self._repo.buscar(consulta)
        sistema = construir_sistema(recuperados, self._catalogo)
        if resultado_espacial.encontrado and resultado_espacial.destino:
            d = resultado_espacial.destino
            sistema += (
                "\n\nCOINCIDENCIA DIRECTA EN EL PLANO\n"
                f"- {d.id}: {d.etiqueta}. {d.detalle}"
            )

        if isinstance(self._proveedor, ProveedorEco):
            self._proveedor.preparar(recuperados)

        historial = conversacion.recientes(self._settings.historial_max_turnos)
        mensajes = [*historial, Mensaje(rol="user", texto=consulta)]

        error: str | None = None
        try:
            bruto = self._proveedor.responder(sistema, mensajes)
        except ErrorProveedor as exc:
            log.error("fallo del proveedor %s: %s", self.proveedor, exc)
            error = str(exc)
            bruto = (
                "Tuve un problema para responder en este momento. Intenta de nuevo en unos "
                "segundos, o busca el lugar directamente en el mapa."
            )

        texto, destino = self._extraer_lugar(bruto, resultado_espacial.destino)
        ms = int((time.perf_counter() - inicio) * 1000)

        return Respuesta(
            texto=texto.strip(),
            destino=destino,
            fragmentos=tuple(recuperados),
            sin_respuesta=self._parece_sin_respuesta(texto, recuperados),
            proveedor=self.proveedor,
            ms=ms,
            error=error,
        )

    def _extraer_lugar(
        self, bruto: str, respaldo: Destino | None
    ) -> tuple[str, Destino | None]:
        destino = respaldo
        for coincidencia in RE_LUGAR.finditer(bruto):
            candidato = self._repo.destino(coincidencia.group(1).upper())
            if candidato is not None:
                destino = candidato
                break
        return RE_LUGAR.sub("", bruto), destino

    @staticmethod
    def _parece_sin_respuesta(texto: str, recuperados: list[FragmentoPuntuado]) -> bool:
        if not recuperados:
            return True
        bajo = texto.lower()
        return any(frase in bajo for frase in FRASES_SIN_RESPUESTA)
