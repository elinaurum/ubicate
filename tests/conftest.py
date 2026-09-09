from __future__ import annotations

from pathlib import Path

import pytest

from ubicate.chat.conocimiento import BaseConocimiento
from ubicate.config import Settings
from ubicate.datos.repositorio import RepositorioCampus

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(dir_datos=RAIZ / "data", dir_kb=RAIZ / "data" / "kb", dir_assets=RAIZ / "assets")


@pytest.fixture(scope="session")
def repo(settings: Settings) -> RepositorioCampus:
    return RepositorioCampus.desde_archivos(settings)


@pytest.fixture(scope="session")
def kb(settings: Settings) -> BaseConocimiento:
    return BaseConocimiento.desde_directorio(settings.dir_kb)
