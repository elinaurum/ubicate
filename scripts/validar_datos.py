#!/usr/bin/env python3
"""Valida los datos del campus y la base de conocimiento.

Se ejecuta en CI antes de cada despliegue y localmente después de cada edición
de ``data/``. Devuelve código 1 si hay algo que impediría arrancar la app o que
degradaría la calidad de las respuestas.

Uso:  python scripts/validar_datos.py [--estricto]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from ubicate.chat.conocimiento import BaseConocimiento  # noqa: E402
from ubicate.config import get_settings  # noqa: E402
from ubicate.datos.repositorio import ErrorDatos, RepositorioCampus  # noqa: E402

OK, AVISO, FALLA = "  ok  ", " aviso", " falla"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--estricto", action="store_true", help="trata los avisos como errores"
    )
    args = parser.parse_args()

    settings = get_settings()
    errores, avisos = 0, 0

    print("Validando datos del campus…")
    try:
        repo = RepositorioCampus.desde_archivos(settings)
    except (ErrorDatos, FileNotFoundError) as exc:
        print(f"[{FALLA}] {exc}")
        return 1

    d = repo.diagnostico
    print(f"[{OK}] {d.edificios} edificios y {d.salas} salas cargados y validados")

    for conflicto in d.conflictos:
        print(f"[{AVISO}] {conflicto}")
        avisos += 1
    for advertencia in d.advertencias:
        print(f"[{AVISO}] {advertencia}")
        avisos += 1

    if not settings.ruta_imagen_mapa.exists():
        print(f"[{FALLA}] falta el plano en {settings.ruta_imagen_mapa}")
        errores += 1
    else:
        print(f"[{OK}] plano del campus presente")

    for planta in repo.plantas():
        salas_dibujadas = repo.salas_en_planta(planta)
        con_forma = sum(1 for s in salas_dibujadas if s.sala.poligono_interior)
        print(
            f"[{OK}] planta {planta.id} (piso {planta.piso}): "
            f"{planta.ancho_m}x{planta.alto_m} m, {len(salas_dibujadas)} salas "
            f"({con_forma} con contorno), {len(planta.puntos)} referencias"
        )
        sin_forma = [s.id for s in salas_dibujadas if not s.sala.poligono_interior]
        if sin_forma:
            print(
                f"[{AVISO}] sin contorno derivable del plano, se dibujan como punto: "
                f"{', '.join(sorted(sin_forma))}"
            )
            avisos += 1

    sin_instrucciones = [
        cid
        for cid, _ in repo.catalogo_mapeable()
        if not (repo.destino(cid).detalle or "").strip()
    ]
    if sin_instrucciones:
        print(f"[{AVISO}] {len(sin_instrucciones)} destinos sin descripción: "
              f"{', '.join(sin_instrucciones[:8])}")
        avisos += 1

    print("\nValidando base de conocimiento…")
    kb = BaseConocimiento.desde_directorio(settings.dir_kb)
    if not kb.fragmentos:
        print(f"[{FALLA}] la base de conocimiento está vacía")
        errores += 1
    else:
        print(f"[{OK}] {len(kb.fragmentos)} fragmentos en {len(kb.documentos)} documentos")

    for doc in kb.documentos:
        if doc.actualizado == "desconocido":
            print(f"[{AVISO}] {doc.id}: sin fecha de actualización en la cabecera")
            avisos += 1
    for doc in kb.vencidos:
        print(f"[{AVISO}] {doc.id}: vigencia vencida ({doc.vigencia})")
        avisos += 1

    print(f"\nResumen: {errores} errores, {avisos} avisos")
    if errores or (args.estricto and avisos):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
