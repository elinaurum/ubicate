"""Registro de uso para priorizar el crecimiento de la base de conocimiento.

Responde a la extensión "instrumentación de uso" de la documentación: saber
qué se pregunta y qué queda sin responder, para decidir con datos y no con
intuición qué contenido cargar después.

Privacidad: no se guarda identidad. La sesión se identifica con un hash
truncado y aleatorio por visita, que no permite reidentificar a la persona ni
enlazar dos visitas distintas. Ver docs/PRIVACIDAD.md.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from ubicate.config import Settings

log = logging.getLogger(__name__)
_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class EventoConsulta:
    ts: str
    sesion: str
    origen: str            # "chat" | "buscador"
    consulta: str
    estado: str            # exacto | ambiguo | sugerencias | vacio | respondido | sin_respuesta
    destino_id: str | None
    ms: int
    proveedor: str | None = None


class RegistroConsultas:
    """Escritura append-only en JSONL. Falla en silencio: nunca tumba la app."""

    def __init__(self, settings: Settings) -> None:
        self._activo = settings.metricas_activas
        self._ruta: Path = settings.ruta_metricas
        if self._activo:
            try:
                self._ruta.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                log.warning("no se pudo preparar el archivo de métricas: %s", exc)
                self._activo = False

    def registrar(
        self,
        *,
        sesion: str,
        origen: str,
        consulta: str,
        estado: str,
        destino_id: str | None = None,
        ms: int = 0,
        proveedor: str | None = None,
    ) -> None:
        if not self._activo:
            return
        evento = EventoConsulta(
            ts=datetime.now(tz=UTC).isoformat(),
            sesion=sesion,
            origen=origen,
            consulta=consulta[:200],
            estado=estado,
            destino_id=destino_id,
            ms=ms,
            proveedor=proveedor,
        )
        linea = json.dumps(asdict(evento), ensure_ascii=False)
        try:
            with _LOCK, self._ruta.open("a", encoding="utf-8") as fh:
                fh.write(linea + "\n")
        except OSError as exc:  # pragma: no cover
            log.warning("no se pudo registrar la consulta: %s", exc)
