#!/usr/bin/env python3
"""Diagnostica la conexión con el proveedor de modelo.

Cuando el chat responde "tuve un problema para responder", la causa real queda
en el log y es fácil de perder. Este script la muestra en pantalla, en español,
con la solución concreta para cada caso.

Uso:  python scripts/probar_proveedor.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from ubicate.chat.proveedores import (  # noqa: E402
    ErrorProveedor,
    Mensaje,
    ProveedorEco,
    crear_proveedor,
)
from ubicate.config import ProveedorLLM, get_settings  # noqa: E402

SEP = "─" * 68

# El propio error suele traer el reemplazo: "Please update your code to use
# models/gemini-3.6-flash". Extraerlo ahorra adivinar en una lista de 51.
RE_SUGERIDO = re.compile(r"use\s+models/([A-Za-z0-9.\-]+)")


def modelo_sugerido(mensaje: str) -> str | None:
    coincidencia = RE_SUGERIDO.search(mensaje)
    return coincidencia.group(1) if coincidencia else None


def diagnostico(mensaje: str) -> str:
    """Traduce el error del servicio a algo accionable."""
    bajo = mensaje.lower()
    if "404" in bajo or "not found" in bajo or "is not found" in bajo:
        sugerido = modelo_sugerido(mensaje)
        if sugerido:
            return (
                "Ese modelo ya no está disponible, y el proveedor indica cuál\n"
                "  usar en su lugar. Pon esta línea en tu archivo .env:\n\n"
                f"      UBICATE_MODELO_LLM={sugerido}\n\n"
                "  Guarda el archivo y vuelve a ejecutar este script."
            )
        return (
            "El nombre del modelo no existe o no está disponible para tu cuenta.\n"
            "  → Corrige UBICATE_MODELO_LLM en tu archivo .env con uno de los\n"
            "    modelos que aparecen listados más abajo."
        )
    if "401" in bajo or "unauthorized" in bajo or "api key" in bajo or "api_key" in bajo:
        return (
            "La API key no es válida o no corresponde a este proveedor.\n"
            "  → Revisa que copiaste la key completa en UBICATE_API_KEY, sin\n"
            "    espacios ni comillas, y que sea del proveedor configurado."
        )
    if "429" in bajo or "quota" in bajo or "rate" in bajo or "exhausted" in bajo:
        return (
            "Se agotó la cuota o pasaste el límite de velocidad.\n"
            "  → Espera un minuto y reintenta. Si se repite seguido, revisa tus\n"
            "    límites en la consola del proveedor."
        )
    if "connection" in bajo or "timeout" in bajo or "getaddrinfo" in bajo:
        return (
            "No se pudo llegar al servidor.\n"
            "  → Revisa tu conexión a internet o si hay un proxy o firewall\n"
            "    de la universidad bloqueando la salida."
        )
    if "permission" in bajo or "403" in bajo:
        return (
            "La key es válida pero no tiene permiso para este modelo.\n"
            "  → Puede que el modelo no esté disponible en la capa gratuita."
        )
    return "  → Copia el mensaje completo de arriba para pedir ayuda."


def listar_modelos(settings) -> None:
    if settings.proveedor_llm is ProveedorLLM.ANTHROPIC:
        print("  (para Anthropic, consulta la lista en su documentación)")
        return
    try:
        from openai import OpenAI

        cliente = OpenAI(api_key=settings.api_key, base_url=settings.base_url_efectiva)
        nombres = sorted(m.id.replace("models/", "") for m in cliente.models.list())
    except Exception as exc:
        print(f"  no se pudo obtener la lista: {exc}")
        return

    descartar = ("embedding", "aqa", "image", "audio", "tts", "video", "computer-use")
    utiles = [n for n in nombres if not any(d in n for d in descartar)]
    # Los de texto rápidos son los adecuados para este proyecto. Se listan de
    # mayor a menor versión porque las antiguas suelen estar cerradas a cuentas
    # nuevas, aunque el listado igual las devuelva.
    recomendados = sorted(
        (n for n in utiles if "flash" in n or "mini" in n or "haiku" in n), reverse=True
    )
    print(f"  {len(utiles)} modelos de texto disponibles. Prueba primero los más nuevos:")
    for nombre in (recomendados or utiles)[:10]:
        print(f"    · {nombre}")
    print()
    print("  Ojo: aparecer en esta lista no garantiza que tu cuenta pueda usarlo.")
    print("  Algunos modelos antiguos están cerrados para cuentas nuevas y")
    print("  devuelven 404 igual. Si pasa, el mensaje de error dice cuál usar.")


def main() -> int:
    settings = get_settings()

    print(SEP)
    print("CONFIGURACIÓN ACTUAL")
    print(SEP)
    print(f"  Proveedor : {settings.proveedor_llm.value}")
    print(f"  Modelo    : {settings.modelo_llm or '(vacío)'}")
    print(f"  Endpoint  : {settings.base_url_efectiva or '(el del proveedor por defecto)'}")
    if settings.api_key:
        k = settings.api_key
        print(f"  API key   : {k[:6]}…{k[-4:]}  ({len(k)} caracteres)")
    else:
        print("  API key   : (vacía)")
    print()

    if settings.proveedor_llm is ProveedorLLM.ECO:
        print("Estás en modo eco: la app responde sin modelo de lenguaje.")
        print("Para activar el chat, configura UBICATE_PROVEEDOR_LLM en tu .env.")
        return 0

    if not settings.api_key:
        print("✗ No hay API key. La app va a funcionar en modo eco.")
        print("  → Agrega UBICATE_API_KEY=tu-key en el archivo .env")
        return 1

    proveedor = crear_proveedor(settings)
    if isinstance(proveedor, ProveedorEco):
        print("✗ No se pudo crear el proveedor; la app cayó a modo eco.")
        print("  → Revisa los avisos de más arriba. Lo más común es que falte")
        print("    la librería: ejecuta  pip install openai")
        return 1

    if not settings.modelo_llm:
        print("✗ UBICATE_MODELO_LLM está vacío. Hay que indicar un modelo.")
        print()
        print("MODELOS DISPONIBLES")
        listar_modelos(settings)
        return 1

    print(SEP)
    print("PROBANDO UNA CONSULTA REAL…")
    print(SEP)
    try:
        respuesta = proveedor.responder(
            "Responde solo con la palabra: funciona",
            [Mensaje(rol="user", texto="hola")],
        )
    except ErrorProveedor as exc:
        print("✗ FALLÓ\n")
        print(f"  Mensaje del servicio:\n  {exc}\n")
        print("  Diagnóstico:")
        print(f"  {diagnostico(str(exc))}\n")
        print(SEP)
        print("MODELOS DISPONIBLES CON TU KEY")
        print(SEP)
        listar_modelos(settings)
        return 1

    print(f"✓ FUNCIONA. El modelo respondió: {respuesta.strip()[:120]!r}")
    print("\n  Ya puedes usar el chat. Si la app está abierta, apágala con Ctrl+C")
    print("  y vuelve a ejecutar:  streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
