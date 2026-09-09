"""Proveedores de generación.

La aplicación no depende de un proveedor concreto: se programa contra el
protocolo ``Proveedor``. Eso permite cambiar de modelo (o quedarse sin API key)
sin tocar la interfaz ni el motor.

``ProveedorEco`` es el modo degradado: no llama a ningún modelo y responde
armando el texto con los fragmentos recuperados. Sirve para desarrollo, para
las pruebas automatizadas y como plan de continuidad si el proveedor externo
se cae o se agota el presupuesto — con 2.000 usuarios eso deja de ser hipótesis.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ubicate.chat.conocimiento import FragmentoPuntuado
from ubicate.config import COMPATIBLES_OPENAI, ProveedorLLM, Settings

log = logging.getLogger(__name__)


class ErrorProveedor(RuntimeError):
    """El proveedor de generación no pudo responder."""


def _es_limite(exc: Exception) -> bool:
    """¿El error es por exceso de cuota o de velocidad (429)?"""
    texto = str(exc).lower()
    return "429" in texto or "rate" in texto or "quota" in texto or "exhausted" in texto


def con_reintento(llamada, intentos: int = 3, espera_base: float = 1.5):
    """Reintenta con espera creciente solo ante límites de velocidad.

    Las capas gratuitas devuelven 429 con facilidad. Un reintento corto evita
    que el usuario vea un error por un pico de un par de segundos. No se
    reintenta ante otros errores: un modelo inexistente no se arregla esperando.
    """
    for intento in range(intentos):
        try:
            return llamada()
        except Exception as exc:
            if not _es_limite(exc) or intento == intentos - 1:
                raise
            espera = espera_base * (2**intento)
            log.warning("límite de velocidad alcanzado; reintento en %.1fs", espera)
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


@dataclass(frozen=True, slots=True)
class Mensaje:
    rol: str  # "user" | "assistant"
    texto: str
    # Metadatos de la respuesta del asistente, para volver a dibujarlos al
    # recargar el historial. Los proveedores solo leen ``rol`` y ``texto``.
    citas: tuple[str, ...] = ()
    lugares: tuple[str, ...] = ()  # ids del catálogo mapeable mencionados


@runtime_checkable
class Proveedor(Protocol):
    nombre: str

    def responder(self, sistema: str, mensajes: list[Mensaje]) -> str: ...


class ProveedorEco:
    """Sin modelo de lenguaje: devuelve los fragmentos recuperados."""

    nombre = "eco"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ultimos: list[FragmentoPuntuado] = []

    def preparar(self, resultados: list[FragmentoPuntuado]) -> None:
        self._ultimos = resultados

    def responder(self, sistema: str, mensajes: list[Mensaje]) -> str:
        del sistema, mensajes
        if not self._ultimos:
            return (
                "No encontré esa información en mi base. Puedes escribir el nombre de "
                "una sala o edificio en el buscador del mapa, o consultar en la Oficina "
                "de Administración Docente (gestiondocente@ing.uchile.cl)."
            )
        partes = ["Esto es lo que tengo registrado:"]
        for r in self._ultimos[:2]:
            texto = r.fragmento.texto.replace("**", "").strip()
            if len(texto) > 700:
                texto = texto[:700].rsplit(" ", 1)[0] + "…"
            partes.append(f"\n**{r.fragmento.titulo}**\n{texto}")
        partes.append("\n_(modo sin modelo de lenguaje: respuesta textual de la base)_")
        return "\n".join(partes)


class ProveedorAnthropic:
    nombre = "anthropic"

    def __init__(self, settings: Settings) -> None:
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise ErrorProveedor(
                "falta la dependencia 'anthropic'; instálala o usa UBICATE_PROVEEDOR_LLM=eco"
            ) from exc
        self._settings = settings
        self._cliente = anthropic.Anthropic(api_key=settings.api_key)

    def responder(self, sistema: str, mensajes: list[Mensaje]) -> str:
        try:
            respuesta = con_reintento(
                lambda: self._cliente.messages.create(
                    model=self._settings.modelo_llm,
                    max_tokens=self._settings.max_tokens,
                    temperature=self._settings.temperatura,
                    system=sistema,
                    messages=[{"role": m.rol, "content": m.texto} for m in mensajes],
                )
            )
        except Exception as exc:  # pragma: no cover - depende del servicio externo
            raise ErrorProveedor(str(exc)) from exc
        return "".join(b.text for b in respuesta.content if getattr(b, "type", "") == "text")


class ProveedorOpenAI:
    """Cliente para cualquier endpoint compatible con la API de OpenAI.

    Sirve para OpenAI, Gemini y Groq: los tres exponen ``/chat/completions``
    con el mismo contrato. Lo único que cambia es la URL base y el modelo.
    """

    def __init__(self, settings: Settings) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise ErrorProveedor(
                "falta la dependencia 'openai'; instálala con `pip install openai` "
                "o usa UBICATE_PROVEEDOR_LLM=eco"
            ) from exc

        base_url = settings.base_url_efectiva
        if settings.proveedor_llm is ProveedorLLM.COMPATIBLE and not base_url:
            raise ErrorProveedor(
                "el proveedor 'compatible' necesita UBICATE_BASE_URL"
            )

        self.nombre = settings.proveedor_llm.value
        self._settings = settings
        self._cliente = OpenAI(api_key=settings.api_key, base_url=base_url)

    def responder(self, sistema: str, mensajes: list[Mensaje]) -> str:
        payload = [{"role": "system", "content": sistema}]
        payload += [{"role": m.rol, "content": m.texto} for m in mensajes]
        try:
            respuesta = con_reintento(
                lambda: self._cliente.chat.completions.create(
                    model=self._settings.modelo_llm,
                    max_tokens=self._settings.max_tokens,
                    temperature=self._settings.temperatura,
                    messages=payload,
                )
            )
        except Exception as exc:  # pragma: no cover
            raise ErrorProveedor(str(exc)) from exc

        eleccion = respuesta.choices[0]
        texto = (eleccion.message.content or "").strip()
        razon = (getattr(eleccion, "finish_reason", "") or "").lower()

        if razon and razon != "stop":
            log.warning("proveedor %s terminó con finish_reason=%r", self.nombre, razon)
        if not texto:
            raise ErrorProveedor(f"el modelo no devolvió texto (finish_reason={razon or 'desconocido'})")
        # Gemini corta la generación cuando detecta que está copiando el
        # contexto casi textual ("recitation"). El texto queda a media frase.
        if razon in {"content_filter", "recitation", "safety"}:
            raise ErrorProveedor(
                f"el modelo bloqueó su propia respuesta (finish_reason={razon}); "
                "suele pasar cuando repite el contexto textualmente en vez de reformularlo"
            )
        return texto


def crear_proveedor(settings: Settings) -> Proveedor:
    """Fábrica con degradación automática a modo eco."""
    if not settings.usa_llm:
        if settings.proveedor_llm is not ProveedorLLM.ECO:
            log.warning(
                "proveedor %s configurado sin API key: se usa modo eco",
                settings.proveedor_llm.value,
            )
        return ProveedorEco(settings)

    try:
        if settings.proveedor_llm is ProveedorLLM.ANTHROPIC:
            return ProveedorAnthropic(settings)
        if settings.proveedor_llm in COMPATIBLES_OPENAI:
            return ProveedorOpenAI(settings)
    except ErrorProveedor as exc:
        log.error("no se pudo inicializar el proveedor: %s — se usa modo eco", exc)
    return ProveedorEco(settings)
