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

Instalar las dependencias (una sola vez; la aplicación no las necesita):

    pip install ezdxf                      # para todo menos --recintos
    pip install numpy scipy pillow matplotlib   # además, para --recintos

Uso:

    # 1. ver qué capas trae el archivo
    python scripts/extraer_planta_dxf.py plano.dxf --listar-capas

    # 2. marco del piso y referencias (baños, ascensores, piscina…)
    python scripts/extraer_planta_dxf.py plano.dxf --puntos

    # 3. el piso completo: todos sus recintos como figuras
    python scripts/extraer_planta_dxf.py plano.dxf --recintos assets/plantas/XXX.geojson

    # 4. ubicar una sala y sacar su contorno rectangular
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

* Las formas salen del plano, no de la imaginación. `--recintos` las
  reconstruye desde los muros trazados; `--contorno` solo entrega un
  rectángulo si la sala resulta ser **rectangular de verdad** (lanza 360 rayos
  y compara el área encerrada con la del rectángulo). Cuando no se puede
  derivar, se informa y la sala queda sin contorno: se dibuja como punto, en
  vez de mostrarle al usuario una forma que no es.
* La correspondencia entre el rótulo del plano ("SALA DE CLASES 04") y el
  código oficial de la sala ("B01") **no se deduce**: hay que confirmarla en
  terreno. Ver docs/DEUDA_DATOS.md D-06.
"""

from __future__ import annotations

import argparse
import json
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

# Solo hacen falta para --recintos; se importan al usarlo para que el resto
# del script funcione sin ellas.
CM_POR_PIXEL = 5.0   # resolución de la grilla al reconstruir recintos
AREA_MIN_M2 = 4.0    # más chico que esto no es un recinto, es una junta

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


def _simplificar(puntos: list[list[float]], eps: float) -> list[list[float]]:
    """Douglas-Peucker: quita los vértices que no cambian la forma."""
    if len(puntos) < 3:
        return puntos
    ini, fin = puntos[0], puntos[-1]
    dx, dy = fin[0] - ini[0], fin[1] - ini[1]
    norma = (dx * dx + dy * dy) ** 0.5
    peor, idx = 0.0, 0
    for i in range(1, len(puntos) - 1):
        p = puntos[i]
        if norma < 1e-9:
            d = ((p[0] - ini[0]) ** 2 + (p[1] - ini[1]) ** 2) ** 0.5
        else:
            d = abs(dy * p[0] - dx * p[1] + fin[0] * ini[1] - fin[1] * ini[0]) / norma
        if d > peor:
            peor, idx = d, i
    if peor > eps:
        return _simplificar(puntos[: idx + 1], eps)[:-1] + _simplificar(puntos[idx:], eps)
    return [ini, fin]


def _ortogonalizar(pts: list[list[float]], tol: float = 0.25) -> list[list[float]]:
    """Endereza los tramos casi horizontales o casi verticales.

    La grilla deja los bordes con dientes de sierra; el edificio es ortogonal
    casi en todas partes, así que enderezarlos se acerca al plano, no se aleja.
    """
    out = [list(p) for p in pts]
    for i in range(len(out) - 1):
        a, b = out[i], out[i + 1]
        if abs(a[1] - b[1]) < tol and abs(a[0] - b[0]) > tol:
            y = (a[1] + b[1]) / 2
            a[1] = b[1] = y
        elif abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) > tol:
            x = (a[0] + b[0]) / 2
            a[0] = b[0] = x
    return [[round(p[0], 2), round(p[1], 2)] for p in out]


def _reconstruir_recintos(msp, x0, y0, x1, y1, unidad_cm: float) -> list[dict]:
    """Recintos del piso, a partir de los muros.

    El plano no trae las salas como figuras cerradas: solo los trazos de sus
    muros. Para obtener cada recinto se dibujan muros, tabiques, puertas y
    ascensores sobre una grilla, se buscan las bolsas de espacio que quedan
    cerradas entre ellos, y se traza el contorno de cada una.
    """
    try:
        import numpy as np
        from PIL import Image, ImageDraw
        from scipy import ndimage
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise SystemExit(
            "Para --recintos faltan librerías. Instálalas con:\n\n"
            "    pip install numpy scipy pillow\n"
        ) from exc
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a_m = unidad_cm / 100
    ancho_px = int((x1 - x0) / CM_POR_PIXEL) + 2
    alto_px = int((y1 - y0) / CM_POR_PIXEL) + 2

    def a_pixel(x, y):
        return ((x - x0) / CM_POR_PIXEL, (y1 - y) / CM_POR_PIXEL)

    imagen = Image.new("1", (ancho_px, alto_px), 0)
    lapiz = ImageDraw.Draw(imagen)
    barreras = CAPAS_MURO | {"PUERTAS-VENTANAS", "ASCENSORES"}
    for e in msp:
        if e.dxf.layer not in barreras:
            continue
        t = e.dxftype()
        try:
            if t == "LINE":
                lapiz.line(
                    [a_pixel(e.dxf.start.x, e.dxf.start.y), a_pixel(e.dxf.end.x, e.dxf.end.y)],
                    fill=1, width=2,
                )
            elif t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
                if e.closed:
                    pts = pts + [pts[0]]
                if len(pts) >= 2:
                    lapiz.line([a_pixel(*p) for p in pts], fill=1, width=2)
            elif t == "ARC":
                c, r = e.dxf.center, e.dxf.radius
                a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                if a1 < a0:
                    a1 += 2 * math.pi
                n = max(6, int((a1 - a0) / 0.15))
                pts = [
                    (c.x + r * math.cos(a0 + (a1 - a0) * i / n),
                     c.y + r * math.sin(a0 + (a1 - a0) * i / n))
                    for i in range(n + 1)
                ]
                lapiz.line([a_pixel(*p) for p in pts], fill=1, width=2)
            elif t == "CIRCLE":
                c, r = e.dxf.center, e.dxf.radius
                px0, py0 = a_pixel(c.x - r, c.y + r)
                px1, py1 = a_pixel(c.x + r, c.y - r)
                lapiz.ellipse([px0, py0, px1, py1], outline=1, width=2)
        except Exception:  # noqa: BLE001
            continue

    muros = ndimage.binary_dilation(np.array(imagen, dtype=bool), iterations=1)
    etiquetas, cuantas = ndimage.label(~muros)
    del_borde = set(etiquetas[0, :]) | set(etiquetas[-1, :])
    del_borde |= set(etiquetas[:, 0]) | set(etiquetas[:, -1])
    del_borde.discard(0)

    m2_por_pixel = CM_POR_PIXEL**2 / 10000.0
    tamanos = ndimage.sum(np.ones_like(etiquetas), etiquetas, range(1, cuantas + 1))
    cajas = ndimage.find_objects(etiquetas)

    recintos: list[dict] = []
    for etiqueta in range(1, cuantas + 1):
        if etiqueta in del_borde or tamanos[etiqueta - 1] * m2_por_pixel < AREA_MIN_M2:
            continue
        caja = cajas[etiqueta - 1]
        if caja is None:
            continue
        sub = np.pad((etiquetas[caja] == etiqueta).astype(float), 2)
        fig = plt.figure()
        ejes = fig.add_subplot(111)
        caminos = [p.vertices for p in ejes.contour(sub, levels=[0.5]).get_paths()
                   if len(p.vertices) >= 4]
        plt.close(fig)
        if not caminos:
            continue
        borde = max(caminos, key=len)
        f0, c0 = caja[0].start - 2, caja[1].start - 2
        pts = [
            [round(float(c0 + p[0]) * CM_POR_PIXEL * a_m, 2),
             round(float(alto_px - (f0 + p[1])) * CM_POR_PIXEL * a_m, 2)]
            for p in borde
        ]
        forma = _ortogonalizar(_simplificar(pts, 0.18))
        limpio = [forma[0]]
        for p in forma[1:]:
            if p != limpio[-1]:
                limpio.append(p)
        if len(limpio) < 4:
            continue
        n = len(limpio)
        area = abs(sum(limpio[i][0] * limpio[(i + 1) % n][1]
                       - limpio[(i + 1) % n][0] * limpio[i][1] for i in range(n))) / 2
        if area >= AREA_MIN_M2:
            recintos.append({"vertices": limpio, "area_m2": round(area, 1)})
    recintos.sort(key=lambda r: -r["area_m2"])
    return recintos


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
        "--recintos",
        type=Path,
        metavar="SALIDA.geojson",
        help="reconstruye los recintos del piso y los escribe como GeoJSON",
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

    if args.recintos:
        print("\nReconstruyendo los recintos del piso… (toma un momento)")
        recintos = _reconstruir_recintos(msp, x0, y0, x1, y1, args.unidad_cm)
        features = [
            {
                "type": "Feature",
                "properties": {"area_m2": r["area_m2"]},
                "geometry": {"type": "Polygon", "coordinates": [r["vertices"] + [r["vertices"][0]]]},
            }
            for r in recintos
        ]
        gj = {
            "type": "FeatureCollection",
            "properties": {
                "fuente": f"Recintos reconstruidos de {args.dxf.name} con "
                          "scripts/extraer_planta_dxf.py --recintos",
                "unidades": "metros, origen abajo-izquierda, [x, y]",
            },
            "features": features,
        }
        args.recintos.parent.mkdir(parents=True, exist_ok=True)
        args.recintos.write_text(
            json.dumps(gj, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8"
        )
        cubierto = sum(r["area_m2"] for r in recintos)
        print(f"  {len(recintos)} recintos, {cubierto:.0f} m2 cubiertos")
        print(f"  escrito en {args.recintos}")
        print("  Recuerda sacar de este archivo los recintos que sean salas del")
        print("  catálogo: esos van como `poligono_interior` en data/salas.json.")

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
