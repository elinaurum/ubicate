#!/usr/bin/env python3
"""Convierte el documento maestro de conocimiento en archivos de ``data/kb/``.

El prototipo tenía toda la información en un único documento pegado al prompt.
Eso impide (a) actualizar por partes, (b) saber qué dato está vencido y
(c) recuperar solo lo pertinente a la pregunta.

Aquí el documento se parte en archivos temáticos con cabecera de metadatos:

    ---
    id: vida_en_campus
    titulo: Vida cotidiana en el campus
    bloque: A
    fuente: levantamiento del equipo U-bícate
    actualizado: 2025-11-01
    vigencia: revisar_semestral
    ---

``vigencia`` admite ``permanente``, ``revisar_semestral`` o ``vence:AAAA-MM-DD``
y es lo que permite avisar cuando un dato quedó obsoleto (limitación L2).

Uso:  python scripts/importar_kb.py [--salida data/kb]
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# (id, título, bloque, vigencia, marcador de inicio en el documento maestro)
SECCIONES = [
    (
        "vida_en_campus",
        "Vida cotidiana, servicios y espacios del campus",
        "A",
        "revisar_semestral",
        "## Informaciones varias",
    ),
    (
        "cuerpo_funcionario",
        "Cuerpo funcionario y unidades de la FCFM",
        "H",
        "revisar_semestral",
        "## Información sobre el cuerpo funcionario de la FCFM:",
    ),
    (
        "franquicias_y_salud",
        "Franquicias médicas y dentales, y salud estudiantil",
        "J",
        "revisar_semestral",
        "## Información sobre franquicias",
    ),
]


def cabecera(sid: str, titulo: str, bloque: str, vigencia: str) -> str:
    return (
        "---\n"
        f"id: {sid}\n"
        f"titulo: {titulo}\n"
        f"bloque: {bloque}\n"
        "fuente: levantamiento del equipo U-bícate sobre canales institucionales FCFM\n"
        f"actualizado: {date.today().isoformat()}\n"
        f"vigencia: {vigencia}\n"
        "---\n\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origen", type=Path, default=Path(__file__).parent / "_kb_origen.md")
    parser.add_argument("--salida", type=Path, default=RAIZ / "data" / "kb")
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    texto = args.origen.read_text(encoding="utf-8")
    cortes: list[int] = []
    for *_, marcador in SECCIONES:
        pos = texto.find(marcador)
        if pos < 0:
            raise SystemExit(f"no se encontró el marcador {marcador!r} en el documento maestro")
        cortes.append(pos)
    cortes.append(len(texto))

    for i, (sid, titulo, bloque, vigencia, _) in enumerate(SECCIONES):
        cuerpo = texto[cortes[i] : cortes[i + 1]].strip()
        destino = args.salida / f"{i + 1:02d}_{sid}.md"
        destino.write_text(cabecera(sid, titulo, bloque, vigencia) + cuerpo + "\n", encoding="utf-8")
        print(f"escrito {destino.relative_to(RAIZ)}  ({len(cuerpo):,} caracteres)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
