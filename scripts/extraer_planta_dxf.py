#!/usr/bin/env python3
"""Extrae de un plano DXF de arquitectura los datos de una ``PlantaInterior``:
el marco del piso en metros, el contorno de cada sala y la posición de las
referencias (baños, ascensores, escaleras, piscina). Ver ADR-0009 y
docs/DATOS.md §6.

Es una herramienta de conversión que se corre **una sola vez por piso**, a
mano. No es parte de la aplicación: ningún módulo de ``src/ubicate`` importa
``ezdxf`` (ver ADR-0001, regla de capas).

El origen es un archivo DWG de arquitectura. Este script necesita **DXF**, no
DWG (formato cerrado que no se puede leer sin AutoCAD). Para exportar: en
AutoCAD, "Guardar como" → "DXF"; o con el visor gratuito DWG TrueView de
Autodesk si no hay AutoCAD a mano.

Instalar la dependencia (una sola vez; la aplicación no la necesita):

    pip install ezdxf

Uso:

    # 1. ver qué capas trae el archivo
    python scripts/extraer_planta_dxf.py plano.dxf --listar-capas

    # 2. marco del piso y referencias (baños, ascensores, piscina…)
    python scripts/extraer_planta_dxf.py plano.dxf --puntos

    # 3. contorno de una sala, dando la posición de su rótulo en el plano
    python scripts/extraer_planta_dxf.py plano.dxf --buscar "SALA DE CLASES"
    python scripts/extraer_planta_dxf.py plano.dxf --contorno 19726,12016

## Sobre la escala

**No confíes en el encabezado del archivo.** Los planos de Beauchef 851
declaran milímetros (`$INSUNITS` = 4) pero están dibujados en **centímetros**:
tomar el encabezado al pie de la letra da un edificio 10 veces más chico
(ACT-010 documenta el error y cómo se detectó). Este script asume centímetros
y, al correr, imprime medidas de control (ancho de puerta, espesor de muro)
para que puedas confirmarlo de un vistazo: una puerta mide 0,8–1,1 m y un muro
0,2–0,3 m. Si esos números salen absurdos, la escala es otra: usa
``--unidad-cm`` para corregirla.

## Sobre inventar

Dos reglas que este script respeta y conviene no saltarse:

* El contorno de una sala solo se entrega si la sala resulta ser **rectangular
  de verdad** (se comprueba lanzando 360 rayos y comparando el área real con
  la del rectángulo). Si no lo es, se informa y la sala queda sin contorno:
  se dibuja como punto, en vez de mostrarle al usuario una forma que no es.
* La correspondencia entre el rótulo del plano ("SALA DE CLASES 04") y el
  código oficial de la sala ("B01") **no se deduce**: hay que confirmarla en
  terreno. Ver docs/DEUDA_DATOS.md D-06.
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path

try:
    import ezdxf
except ImportError as exc:
    print(
        "Falta la librería para leer DXF. Instálala con:\n\n"
        "    pip install ezdxf\n\n"
        "(Es solo para esta herramienta; la aplicación no la necesita.)",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

# Capas que definen el espacio construido. El resto del plano (cotas, pilotes,
# ductos de climatización, terreno…) es detalle de construcción.
CAPAS_MURO = {"MUROS", "TABIQUES"}
CAPA_TEXTO = "TEXTO"

# Rótulos del plano que corresponden a cada tipo de referencia de
# ``modelos.TipoPunto``. Se comparan en mayúsculas.
CATEGORIAS: list[tuple[str, tuple[str, ...]]] = [
    ("piscina", ("PISCINA",)),
    ("camarin", ("CAMARIN",)),
    ("ascensor", ("ASCENSOR",)),
    ("escalera", ("ESCALERA",)),
    ("bano", ("VESTIBULO BAÑO", "BAÑO DOC")),
]

TOL = 1.0          # tolerancia para considerar un segmento vertical/horizontal
MAX_RAYO = 2000    # largo máximo de un rayo, en unidades de dibujo
RAZON_RECTA = 0.97  # área real / área del rectángulo para aceptar el contorno


def _segmentos_de_muro(msp) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segmentos = []
    for e in msp:
        if e.dxf.layer not in CAPAS_MURO:
            continue
        t = e.dxftype()
        try:
            if t == "LINE":
                segmentos.append(
                    ((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
                )
            elif t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
                seq = pts + [pts[0]] if e.closed else pts
                segmentos.extend(zip(seq, seq[1:], strict=False))
        except Exception:  # noqa: BLE001 - entidad sin la geometría esperada
            continue
    return segmentos


def _marco(msp) -> tuple[float, float, float, float]:
    """Envolvente de los muros: el marco del piso, sin los rótulos de calles."""
    xs: list[float] = []
    ys: list[float] = []
    for (x1, y1), (x2, y2) in _segmentos_de_muro(msp):
        xs += [x1, x2]
        ys += [y1, y2]
    if not xs:
        raise ValueError(f"no hay geometría en las capas {sorted(CAPAS_MURO)}")
    return min(xs), max(xs), min(ys), max(ys)


def _corta(px, py, dx, dy, a, b) -> float | None:
    (x1, y1), (x2, y2) = a, b
    sx, sy = x2 - x1, y2 - y1
    den = dx * sy - dy * sx
    if abs(den) < 1e-9:
        return None
    t = ((x1 - px) * sy - (y1 - py) * sx) / den
    u = ((x1 - px) * dy - (y1 - py) * dx) / den
    return t if (t > 1e-6 and -1e-9 <= u <= 1 + 1e-9) else None


def _golpe_ortogonal(segmentos, px, py, dx, dy) -> float | None:
    """Distancia al muro más cercano en una dirección recta."""
    mejor = None
    for (x1, y1), (x2, y2) in segmentos:
        if dx != 0:
            if abs(x1 - x2) > TOL or not (min(y1, y2) - TOL <= py <= max(y1, y2) + TOL):
                continue
            d = (x1 - px) * dx
        else:
            if abs(y1 - y2) > TOL or not (min(x1, x2) - TOL <= px <= max(x1, x2) + TOL):
                continue
            d = (y1 - py) * dy
        if d > TOL and (mejor is None or d < mejor):
            mejor = d
    return mejor


def _area(puntos) -> float:
    n = len(puntos)
    return abs(
        sum(puntos[i][0] * puntos[(i + 1) % n][1] - puntos[(i + 1) % n][0] * puntos[i][1]
            for i in range(n))
    ) / 2


def _area_visible(segmentos, px, py, n_rayos: int = 360) -> float:
    """Área realmente encerrada por los muros alrededor del punto."""
    puntos = []
    for i in range(n_rayos):
        ang = 2 * math.pi * i / n_rayos
        dx, dy = math.cos(ang), math.sin(ang)
        mejor = None
        for seg in segmentos:
            (x1, y1), (x2, y2) = seg
            if (max(x1, x2) < px - MAX_RAYO or min(x1, x2) > px + MAX_RAYO
                    or max(y1, y2) < py - MAX_RAYO or min(y1, y2) > py + MAX_RAYO):
                continue
            t = _corta(px, py, dx, dy, *seg)
            if t is not None and (mejor is None or t < mejor):
                mejor = t
        mejor = MAX_RAYO if mejor is None else mejor
        puntos.append((px + dx * mejor, py + dy * mejor))
    return _area(puntos)


def _texto_de(e) -> str | None:
    if e.dxftype() == "MTEXT":
        return e.plain_text()
    if e.dxftype() == "TEXT":
        try:
            return e.dxf.text
        except Exception:  # noqa: BLE001
            return None
    return None


def _control_de_escala(msp, unidad_cm: float) -> None:
    """Medidas conocidas, para confirmar de un vistazo que la escala es la correcta."""
    anchos = []
    for e in msp:
        if e.dxf.layer != "PUERTAS-VENTANAS" or e.dxftype() != "LWPOLYLINE":
            continue
        try:
            pts = [(p[0], p[1]) for p in e.get_points()]
        except Exception:  # noqa: BLE001
            continue
        ancho = max(
            max(p[0] for p in pts) - min(p[0] for p in pts),
            max(p[1] for p in pts) - min(p[1] for p in pts),
        )
        if 50 < ancho < 200:
            anchos.append(ancho)
    if anchos:
        m = statistics.median(anchos) * unidad_cm / 100
        estado = "verosímil" if 0.7 <= m <= 1.3 else "SOSPECHOSO"
        print(f"  control: ancho típico de puerta = {m:.2f} m  ({estado}; se espera 0,8-1,1 m)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("dxf", type=Path, help="archivo DXF de entrada (no DWG)")
    parser.add_argument("--listar-capas", action="store_true", help="lista las capas y sale")
    parser.add_argument("--puntos", action="store_true", help="lista las referencias del piso")
    parser.add_argument("--buscar", help="busca un texto y muestra su posición en metros")
    parser.add_argument(
        "--contorno",
        help="contorno de la sala que contiene este punto del dibujo, como x,y",
    )
    parser.add_argument(
        "--unidad-cm",
        type=float,
        default=1.0,
        help="cuántos centímetros vale una unidad del dibujo (por defecto 1)",
    )
    args = parser.parse_args()

    if not args.dxf.exists():
        print(f"No existe el archivo {args.dxf}", file=sys.stderr)
        return 1

    doc = ezdxf.readfile(str(args.dxf))
    msp = doc.modelspace()

    if args.listar_capas:
        from collections import Counter

        for capa, n in Counter(e.dxf.layer for e in msp).most_common():
            print(f"{capa}: {n}")
        return 0

    x0, x1, y0, y1 = _marco(msp)
    a_m = args.unidad_cm / 100

    def local(x: float, y: float) -> list[float]:
        """(x,y) del dibujo -> [y, x] en metros del piso, origen abajo-izquierda."""
        return [round(float(y - y0) * a_m, 2), round(float(x - x0) * a_m, 2)]

    print(f'Marco del piso: ancho_m = {round((x1 - x0) * a_m, 2)}, '
          f'alto_m = {round((y1 - y0) * a_m, 2)}')
    print(f"  origen del dibujo: ({x0:.0f}, {y0:.0f});  1 unidad = {args.unidad_cm} cm")
    _control_de_escala(msp, args.unidad_cm)

    if args.buscar:
        objetivo = args.buscar.upper()
        print(f"\nCoincidencias de {args.buscar!r}  (posición [y, x] en metros):")
        for e in msp:
            if e.dxf.layer != CAPA_TEXTO:
                continue
            txt = _texto_de(e)
            if txt and objetivo in txt.upper():
                p = e.dxf.insert
                print(f"  {' '.join(txt.split())!r}: {local(p.x, p.y)}"
                      f"   (dibujo: {p.x:.0f},{p.y:.0f})")

    if args.puntos:
        print("\nReferencias del piso, para el campo `puntos` de plantas.json:")
        vistos = set()
        for e in msp:
            if e.dxf.layer != CAPA_TEXTO:
                continue
            txt = _texto_de(e)
            if not txt:
                continue
            limpio = " ".join(txt.split())
            for tipo, claves in CATEGORIAS:
                if any(k in limpio.upper() for k in claves):
                    p = e.dxf.insert
                    coord = local(p.x, p.y)
                    clave = (limpio, tuple(coord))
                    if clave not in vistos:
                        vistos.add(clave)
                        print(f'  {{"nombre": "{limpio}", "tipo": "{tipo}", '
                              f'"coord": {coord}}},')
                    break

    if args.contorno:
        px, py = (float(v) for v in args.contorno.split(","))
        segmentos = _segmentos_de_muro(msp)
        izq = _golpe_ortogonal(segmentos, px, py, -1, 0)
        der = _golpe_ortogonal(segmentos, px, py, 1, 0)
        aba = _golpe_ortogonal(segmentos, px, py, 0, -1)
        arr = _golpe_ortogonal(segmentos, px, py, 0, 1)
        print(f"\nContorno alrededor de ({px:.0f}, {py:.0f}):")
        if None in (izq, der, aba, arr):
            print("  el punto no queda cerrado por muros en las cuatro direcciones.")
            print("  -> sin contorno: cargar solo coord_interior y dibujar como punto.")
            return 0
        rect = (izq + der) * (aba + arr)
        razon = _area_visible(segmentos, px, py) / rect
        print(f"  medidas: {(izq + der) * a_m:.2f} x {(aba + arr) * a_m:.2f} m")
        print(f"  área encerrada / área del rectángulo = {razon:.3f}")
        if razon >= RAZON_RECTA:
            poli = [
                local(px - izq, py - aba),
                local(px + der, py - aba),
                local(px + der, py + arr),
                local(px - izq, py + arr),
            ]
            print(f'  "poligono_interior": {poli}')
        else:
            print("  la sala NO es rectangular: el rectángulo no la representa.")
            print("  -> sin contorno: cargar solo coord_interior y dibujar como punto.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
