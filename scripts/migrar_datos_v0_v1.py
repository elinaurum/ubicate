#!/usr/bin/env python3
"""Migra los JSON del prototipo (v0) al esquema v1.

Se deja como script y no como edición manual para que la transformación sea
reproducible y auditable. Cambios que aplica:

1. Agrega ``acceso`` ("850"/"851") a cada edificio, reemplazando el hack de
   mirar el prefijo del id en tiempo de ejecución.
2. Agrega ``tipo`` a edificios (edificio / acceso / deportivo / servicio).
3. Convierte ``piso`` de string a entero en salas.
4. Poda los alias que solo eran variantes ortográficas (mayúsculas, guiones,
   espacios): la normalización de búsqueda ya los cubre. Conserva únicamente
   los alias semánticos ("gorbea", "civil", "csn"...).
5. Repara los alias corruptos de las salas E1xx/E2xx, que en v0 contenían
   comillas tipográficas dentro del string.
6. Elimina el alias ambiguo "auditorio", que apuntaba a dos edificios
   distintos (Gorbea en 850 y d'Etigny en 851).
7. Fusiona la sala ``GORBEA_SALA`` con el edificio ``850_AUDITORIO``: eran el
   mismo lugar físico duplicado en dos tablas, y competían por la misma clave
   de búsqueda ("gorbea"). Las instrucciones de acceso pasan a la descripción
   del edificio.

Uso:  python scripts/migrar_datos_v0_v1.py [--salida data/]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from ubicate.busqueda.normalizacion import clave  # noqa: E402

# Edificios que pertenecen al sector Beauchef 851.
SECTOR_851 = {
    "851_INDUS", "851_AUDITORIO", "851_INGMEC", "851_INGQUIM",
    "851_INGMAT", "851_CS_COMPUTACION", "851_CMM", "ACCESO_851",
}

TIPOS = {
    "ACCESO_850": "acceso",
    "ACCESO_851": "acceso",
    "850_CANCHA": "deportivo",
    "850_CAFETERIA": "servicio",
    "850_CASINO": "servicio",
    "850_BIBLIOTECA": "servicio",
    "850_AUDITORIO": "servicio",
    "851_AUDITORIO": "servicio",
}

# Alias semánticos que se conservan o corrigen explícitamente.
# Salas que en v0 duplicaban un edificio ya existente: sala -> edificio destino.
SALAS_FUSIONADAS = {"GORBEA_SALA": "850_AUDITORIO"}

ALIAS_MANUALES = {
    "850_AUDITORIO": ["gorbea", "auditorio gorbea"],
    "851_AUDITORIO": ["etigny", "detigny", "auditorio detigny", "la arana", "araña"],
    "850_CANCHA": ["cancha 850", "multicancha"],
    "850_CAFETERIA": ["cafeteria 850"],
    "850_CASINO": ["casino", "domeyko", "comesanito"],
    "851_INGQUIM": ["quimica", "biotecnologia", "materiales"],
    "850_AMTC": ["amtc"],
    "850_CENER": ["centro de energia"],
    "850_HALL": ["hall sur", "pajarera"],
}


def alias_utiles(entidad_id: str, nombre: str, aliases: list[str]) -> list[str]:
    """Conserva solo los alias que aportan información nueva."""
    if entidad_id in ALIAS_MANUALES:
        return ALIAS_MANUALES[entidad_id]

    redundantes = {clave(entidad_id), clave(nombre)}
    resultado: list[str] = []
    for bruto in aliases:
        # Repara strings corruptos del tipo:  E-111”, “e 111
        for parte in str(bruto).replace("”", '"').replace("“", '"').split(","):
            parte = parte.strip().strip('"').strip()
            if not parte:
                continue
            k = clave(parte)
            if not k or k in redundantes:
                continue
            redundantes.add(k)
            resultado.append(parte)
    return resultado


def migrar_edificios(origen: Path, instrucciones_fusionadas: dict[str, str]) -> list[dict]:
    datos = json.loads(origen.read_text(encoding="utf-8"))
    salida = []
    for e in datos:
        eid = e["id"]
        descripcion = e.get("descripcion", "")
        if eid in instrucciones_fusionadas:
            descripcion = f"{descripcion} {instrucciones_fusionadas[eid]}".strip()
        salida.append(
            {
                "id": eid,
                "nombre": e["nombre"],
                "tipo": TIPOS.get(eid, "edificio"),
                "acceso": "851" if eid in SECTOR_851 else "850",
                "coord": e["coord"],
                "aliases": alias_utiles(eid, e["nombre"], e.get("aliases", [])),
                "descripcion": descripcion,
                "activo": True,
            }
        )
    return salida


def migrar_salas(origen: Path) -> tuple[list[dict], dict[str, str]]:
    datos = json.loads(origen.read_text(encoding="utf-8"))
    salida: list[dict] = []
    fusionadas: dict[str, str] = {}
    for s in datos:
        sid = s["id"]
        if sid in SALAS_FUSIONADAS:
            fusionadas[SALAS_FUSIONADAS[sid]] = s["instrucciones"]
            continue
        salida.append(
            {
                "id": sid,
                "edificio_id": s["edificio_id"],
                "piso": int(str(s["piso"]).replace("−", "-")),
                "tipo": "auditorio" if "GORBEA" in sid else "clase",
                "aliases": alias_utiles(sid, sid, s.get("aliases", [])),
                "instrucciones": s["instrucciones"],
                "activo": True,
            }
        )
    return salida, fusionadas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ / "data")
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    aqui = Path(__file__).parent
    salas, fusionadas = migrar_salas(aqui / "_salas_v0.json")
    edificios = migrar_edificios(aqui / "_edificios_v0.json", fusionadas)

    for nombre, contenido in (("edificios.json", edificios), ("salas.json", salas)):
        destino = args.salida / nombre
        destino.write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"escrito {destino.relative_to(RAIZ)}  ({len(contenido)} registros)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
