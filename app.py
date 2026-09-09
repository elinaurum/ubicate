"""Lanzador de U-bícate.

Mantiene ``streamlit run app.py`` en la raíz del repositorio mientras el código
vive en ``src/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ubicate.ui.app import main  # noqa: E402

main()
