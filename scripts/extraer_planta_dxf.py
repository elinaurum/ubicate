#!/usr/bin/env python3
"""Extrae de un plano DXF de arquitectura las capas útiles para orientarse
(muros, tabiques, puertas/ventanas, ascensores, texto) y las renderiza a PNG,
listas para usar como imagen de una ``PlantaInterior`` (ver ADR-0009,
docs/DATOS.md §6).

Es una herramienta de conversión que se corre **una sola vez por piso**, a
mano. No es parte de la aplicación: ningún módulo de ``src/ubicate`` importa
``ezdxf`` ni ``matplotlib`` (ver ADR-0001, regla de capas).

El origen del plano es un archivo DWG de arquitectura. Este script necesita
**DXF**, no DWG (formato cerrado que no se puede leer sin AutoCAD). Para
exportar: en AutoCAD, "Guardar como" → "DXF"; o con el visor gratuito
DWG TrueView de Autodesk si no hay AutoCAD a mano.

Instalar las dependencias (una sola vez, no se necesitan para correr la
aplicación):

    pip install ezdxf matplotlib

Uso:

    python scripts/extraer_planta_dxf.py plano.dxf --salida assets/plantas/851_piso_-2.png

    # para ubicar el texto de una sala nueva y sacar sus coordenadas:
    python scripts/extraer_planta_dxf.py plano.dxf --buscar "SALA DE CLASES"

La salida imprime el ancho y alto reales en metros: van directo en
``ancho_m``/``alto_m`` de la entrada correspondiente en ``data/plantas.json``.
Las coordenadas que imprime ``--buscar`` (en milímetros, sistema del DXF) hay
que restarles el mínimo que también se imprime, y dividir por 1000, para
obtener el ``coord_interior`` en metros de una sala — ver la función
``a_metros_local`` de este mismo script.

**No inventar la correspondencia entre el código oficial de una sala (p. ej.
B01) y el rótulo que trae el plano** (p. ej. "SALA DE CLASES 04"): hay que
confirmarla en terreno. Ver docs/DEUDA_DATOS.md D-06.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import ezdxf
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
except ImportError as exc:
    print(
        "Faltan las librerías para leer DXF. Instálalas con:\n\n"
        "    pip install ezdxf matplotlib\n\n"
        "(Esto es solo para esta herramienta; la aplicación no las necesita.)",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

# Capas del plano de arquitectura que sirven para orientarse. El resto
# (cotas, pilotes, ductos de climatización, instalaciones, terreno…) es
# detalle de construcción que no aporta y satura el dibujo. Ajustar esta
# lista si un piso nuevo usa nombres de capa distintos — revisar primero con
# --listar-capas.
CAPAS_UTIL = {"MUROS", "TABIQUES", "PUERTAS-VENTANAS", "ASCENSORES", "TEXTO"}


def _bbox_manual(entidades) -> tuple[float, float, float, float]:
    """Extremos (xmin, xmax, ymin, ymax) en mm.

    A mano y no con ``ezdxf.bbox.extents``: esa función no capturó bien las
    polilíneas con arcos de los planos de Beauchef 851 (daba una caja mucho
    más chica que la real). Ver ACT-009.
    """
    xs: list[float] = []
    ys: list[float] = []
    for e in entidades:
        t = e.dxftype()
        try:
            if t == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif t == "LWPOLYLINE":
                for p in e.get_points():
                    xs.append(p[0])
                    ys.append(p[1])
            elif t in ("CIRCLE", "ARC"):
                c, r = e.dxf.center, e.dxf.radius
                xs += [c.x - r, c.x + r]
                ys += [c.y - r, c.y + r]
            elif t in ("TEXT", "MTEXT", "INSERT"):
                xs.append(e.dxf.insert.x)
                ys.append(e.dxf.insert.y)
            elif t == "POINT":
                xs.append(e.dxf.location.x)
                ys.append(e.dxf.location.y)
        except Exception:  # noqa: BLE001 - entidad sin la geometría esperada, se ignora
            continue
    if not xs:
        raise ValueError("ninguna entidad de las capas elegidas tiene geometría reconocible")
    return min(xs), max(xs), min(ys), max(ys)


def _texto_de(entidad) -> str | None:
    if entidad.dxftype() == "MTEXT":
        return entidad.plain_text()
    if entidad.dxftype() == "TEXT":
        try:
            return entidad.dxf.text
        except Exception:  # noqa: BLE001
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dxf", type=Path, help="archivo DXF de entrada (no DWG)")
    parser.add_argument("--salida", type=Path, help="PNG de salida")
    parser.add_argument(
        "--capas",
        help=f"capas a incluir, separadas por coma (por defecto: {','.join(sorted(CAPAS_UTIL))})",
    )
    parser.add_argument("--listar-capas", action="store_true", help="lista las capas del archivo y sale")
    parser.add_argument("--buscar", help="busca este texto entre las capas elegidas y muestra su posición")
    args = parser.parse_args()

    if not args.dxf.exists():
        print(f"No existe el archivo {args.dxf}", file=sys.stderr)
        return 1

    doc = ezdxf.readfile(str(args.dxf))
    msp = doc.modelspace()

    if args.listar_capas:
        from collections import Counter

        conteo = Counter(e.dxf.layer for e in msp)
        for capa, n in conteo.most_common():
            print(f"{capa}: {n}")
        return 0

    capas = {c.strip() for c in args.capas.split(",")} if args.capas else CAPAS_UTIL
    entidades = [e for e in msp if e.dxf.layer in capas]
    if not entidades:
        print(f"Ninguna entidad en las capas {capas}. Prueba --listar-capas.", file=sys.stderr)
        return 1

    xmin, xmax, ymin, ymax = _bbox_manual(entidades)
    ancho_m, alto_m = (xmax - xmin) / 1000, (ymax - ymin) / 1000
    print(f"Tamaño real: {ancho_m:.2f} x {alto_m:.2f} m  (ancho_m x alto_m)")
    print(f"Origen (xmin, ymin) en mm, para restar a otras coordenadas: ({xmin:.1f}, {ymin:.1f})")

    if args.buscar:
        objetivo = args.buscar.upper()
        print(f"\nCoincidencias de {args.buscar!r} (posición en metros locales [y, x]):")
        for e in entidades:
            txt = _texto_de(e)
            if txt and objetivo in txt.upper():
                pos = e.dxf.insert
                y_m = round((pos.y - ymin) / 1000, 2)
                x_m = round((pos.x - xmin) / 1000, 2)
                print(f"  {txt.strip()!r}: [{y_m}, {x_m}]")

    if args.salida:
        fig = plt.figure(figsize=(28, 28 * (ymax - ymin) / (xmax - xmin)))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal")
        ax.axis("off")
        backend = MatplotlibBackend(ax)
        Frontend(RenderContext(doc), backend).draw_entities(entidades)
        backend.finalize()
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.salida, dpi=150, facecolor="white", pad_inches=0)
        plt.close(fig)
        print(f"\nImagen guardada en {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
