"""Configuración de logging estructurado."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from ubicate.config import Settings

_CONFIGURADO = False


class FormatoJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
        }
        if record.exc_info:
            payload["excepcion"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configurar(settings: Settings) -> None:
    """Idempotente: se puede llamar en cada rerun de Streamlit sin duplicar."""
    global _CONFIGURADO
    if _CONFIGURADO:
        return

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_formato == "json":
        handler.setFormatter(FormatoJSON())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s — %(message)s")
        )

    raiz = logging.getLogger("ubicate")
    raiz.handlers.clear()
    raiz.addHandler(handler)
    raiz.setLevel(settings.log_nivel)
    raiz.propagate = False
    _CONFIGURADO = True
