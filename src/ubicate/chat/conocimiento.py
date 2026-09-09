"""Base de conocimiento: carga, fragmentación y recuperación.

Sustituye el volcado completo del documento maestro en el prompt por una
recuperación BM25 de los fragmentos pertinentes. Beneficios:

* el prompt deja de crecer con la base (costo por consulta acotado);
* cada respuesta queda atribuida a fragmentos concretos y citables;
* los fragmentos vencidos se marcan y el modelo recibe la advertencia.

BM25 está implementado a mano, en Python puro: la base son decenas de miles de
caracteres, no millones, y evitar una dependencia de embeddings mantiene el
despliegue simple y sin costo por consulta.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ubicate.busqueda.normalizacion import tokens as _tokens

log = logging.getLogger(__name__)

K1 = 1.5
B = 0.75
MIN_CARACTERES = 60
RE_TITULO = re.compile(r"^\s*(?:#{1,6}\s*)?\*\*(.+?)\*\*")

# Palabras de pregunta y muletillas que no distinguen un fragmento de otro. Se
# suman a las vacías de la normalización, que están pensadas para "sala B04" y
# no para prosa: sin esto, "¿dónde puedo estudiar?" recupera cualquier fragmento
# cuyo título empiece con "¿Dónde puedo…?" (ping pong incluido).
VACIAS_TEXTO = frozenset(
    {
        "puedo", "puede", "pueden", "podria", "podrias", "necesito", "necesitas",
        "quisiera", "tengo", "hay", "como", "cuando", "cuanto", "cuanta",
        "cuantos", "cuantas", "cual", "cuales", "que", "quien", "quienes",
        "sirve", "seria", "estoy", "voy", "van", "ver", "saber", "algun",
        "alguna", "alguno", "este", "esta", "esto", "aca", "aqui", "alla",
        "campus", "facultad", "beauchef", "fcfm", "uchile",
    }
)


def tokens_texto(texto: str) -> list[str]:
    """Tokens para la recuperación sobre la base: sin palabras de pregunta."""
    return [t for t in _tokens(texto) if len(t) > 2 and t not in VACIAS_TEXTO]


@dataclass(frozen=True, slots=True)
class Documento:
    id: str
    titulo: str
    bloque: str
    fuente: str
    actualizado: str
    vigencia: str
    ruta: Path

    @property
    def vencido(self) -> bool:
        if self.vigencia.startswith("vence:"):
            try:
                return date.fromisoformat(self.vigencia.split(":", 1)[1].strip()) < date.today()
            except ValueError:
                return False
        return False


@dataclass(frozen=True, slots=True)
class Fragmento:
    id: str
    titulo: str
    texto: str
    documento: Documento

    @property
    def cita(self) -> str:
        return f"{self.documento.titulo} › {self.titulo}"


@dataclass(frozen=True, slots=True)
class FragmentoPuntuado:
    fragmento: Fragmento
    puntaje: float


def _leer_cabecera(texto: str) -> tuple[dict[str, str], str]:
    if not texto.startswith("---"):
        return {}, texto
    fin = texto.find("\n---", 3)
    if fin < 0:
        return {}, texto
    meta: dict[str, str] = {}
    for linea in texto[3:fin].strip().splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            meta[clave.strip()] = valor.strip()
    return meta, texto[fin + 4 :].lstrip("\n")


def _titulo_de(parrafo: str, respaldo: str) -> str:
    """Título legible del fragmento, a partir de su primera línea."""
    lineas = [linea for linea in parrafo.splitlines() if linea.strip()]
    primera = lineas[0] if lineas else parrafo
    if len(primera.lstrip("#- ").strip()) < 25 and len(lineas) > 1:
        primera = f"{primera.lstrip('#- ').strip()} — {lineas[1]}"
    m = RE_TITULO.match(primera)
    if m:
        titulo = m.group(1).strip().rstrip(":").strip()
        if titulo:
            return titulo[:120]
    limpio = primera.lstrip("#- ").strip().replace("**", "")
    return (limpio[:90] + "…") if len(limpio) > 90 else (limpio or respaldo)


def fragmentar(documento: Documento, cuerpo: str) -> list[Fragmento]:
    """Un fragmento por párrafo, uniendo los demasiado cortos con el anterior."""
    fragmentos: list[Fragmento] = []
    acumulado = ""
    for parrafo in (p.strip() for p in cuerpo.split("\n\n")):
        if not parrafo:
            continue
        acumulado = f"{acumulado}\n\n{parrafo}".strip() if acumulado else parrafo
        if len(acumulado) < MIN_CARACTERES:
            continue
        fragmentos.append(
            Fragmento(
                id=f"{documento.id}#{len(fragmentos):03d}",
                titulo=_titulo_de(acumulado, documento.titulo),
                texto=acumulado,
                documento=documento,
            )
        )
        acumulado = ""
    if acumulado:
        fragmentos.append(
            Fragmento(
                id=f"{documento.id}#{len(fragmentos):03d}",
                titulo=_titulo_de(acumulado, documento.titulo),
                texto=acumulado,
                documento=documento,
            )
        )
    return fragmentos


class BaseConocimiento:
    def __init__(self, fragmentos: list[Fragmento]) -> None:
        self.fragmentos = fragmentos
        self._tokens: list[Counter] = []
        self._largos: list[int] = []
        self._df: Counter = Counter()

        for f in fragmentos:
            t = tokens_texto(f"{f.titulo} {f.texto}")
            contador = Counter(t)
            self._tokens.append(contador)
            self._largos.append(max(len(t), 1))
            self._df.update(contador.keys())

        self._n = max(len(fragmentos), 1)
        self._largo_medio = sum(self._largos) / self._n if fragmentos else 1.0

    # ------------------------------------------------------------------ carga
    @classmethod
    def desde_directorio(cls, directorio: Path) -> BaseConocimiento:
        fragmentos: list[Fragmento] = []
        if not directorio.exists():
            log.warning("no existe el directorio de conocimiento %s", directorio)
            return cls([])

        for archivo in sorted(directorio.glob("*.md")):
            meta, cuerpo = _leer_cabecera(archivo.read_text(encoding="utf-8"))
            documento = Documento(
                id=meta.get("id", archivo.stem),
                titulo=meta.get("titulo", archivo.stem),
                bloque=meta.get("bloque", "?"),
                fuente=meta.get("fuente", "sin fuente declarada"),
                actualizado=meta.get("actualizado", "desconocido"),
                vigencia=meta.get("vigencia", "permanente"),
                ruta=archivo,
            )
            if documento.vencido:
                log.warning("documento vencido en la base: %s", documento.id)
            fragmentos.extend(fragmentar(documento, cuerpo))

        log.info("base de conocimiento: %d fragmentos de %s", len(fragmentos), directorio)
        return cls(fragmentos)

    # ------------------------------------------------------------ recuperación
    def _idf(self, termino: str) -> float:
        df = self._df.get(termino, 0)
        return math.log(1 + (self._n - df + 0.5) / (df + 0.5))

    def buscar(self, consulta: str, k: int = 6) -> list[FragmentoPuntuado]:
        consulta_tokens = tokens_texto(consulta)
        if not consulta_tokens or not self.fragmentos:
            return []

        puntajes: list[tuple[float, int]] = []
        for i, contador in enumerate(self._tokens):
            total = 0.0
            for termino in consulta_tokens:
                tf = contador.get(termino, 0)
                if not tf:
                    continue
                norma = 1 - B + B * (self._largos[i] / self._largo_medio)
                total += self._idf(termino) * (tf * (K1 + 1)) / (tf + K1 * norma)
            if total > 0:
                puntajes.append((total, i))

        puntajes.sort(reverse=True)
        return [
            FragmentoPuntuado(fragmento=self.fragmentos[i], puntaje=round(p, 3))
            for p, i in puntajes[:k]
        ]

    @property
    def documentos(self) -> list[Documento]:
        vistos: dict[str, Documento] = {}
        for f in self.fragmentos:
            vistos.setdefault(f.documento.id, f.documento)
        return list(vistos.values())

    @property
    def vencidos(self) -> list[Documento]:
        return [d for d in self.documentos if d.vencido]
