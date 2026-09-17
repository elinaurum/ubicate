"""Identidad visual de U-bícate, en un solo lugar.

Los colores y las piezas comunes (la chincheta, la cabecera) salen de la
maqueta que hizo el equipo. Viven aquí y no repartidos por los componentes:
cambiar el rojo de la marca tiene que ser editar una línea, no buscar el
mismo `#E63329` en cinco archivos.

Los colores base también están en `.streamlit/config.toml`, que es lo que
Streamlit usa para sus propios controles. **Si cambias uno aquí, cámbialo
también allá**: son los mismos valores desde dos lados.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

# --- Paleta de la maqueta ---------------------------------------------------
NAVY = "#2C3E5C"          # fondo de la aplicación y de la cabecera
NAVY_CLARO = "#3A4E70"    # superficies sobre el fondo (desplegables, avisos)
ROJO = "#E63329"          # la marca: chincheta y acción principal
ROJO_OSCURO = "#C42A21"
AZUL_MEDIO = "#7391B5"    # acción secundaria
AZUL_BURBUJA = "#3F5C86"  # burbujas del asistente: el de la maqueta deja el
                          # texto blanco en 3,3:1 de contraste, ilegible.
                          # Este llega a 6,5:1 sin salirse de la familia.
AZUL_CLARO = "#8AA5C4"
BLANCO = "#FFFFFF"        # tarjetas: mapa y conversación
GRIS_BURBUJA = "#E4E6E9"  # burbujas de quien pregunta
GRIS_TEXTO = "#9AA5B1"    # textos de relleno en campos


def chincheta(alto: int = 56) -> str:
    """La chincheta con la U, como SVG en línea.

    Va incrustada y no como archivo: no agrega una petición ni un asset que
    mantener, y hereda el color de la paleta de arriba.
    """
    ancho = round(alto * 104 / 124)
    return (
        f'<svg width="{ancho}" height="{alto}" viewBox="0 0 104 124" fill="none" '
        'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="U-bícate">'
        '<path d="M52 0C23.3 0 0 23.3 0 52c0 31.8 41.6 66.9 48.3 72.3a5.9 5.9 0 '
        f'0 0 7.4 0C62.4 118.9 104 83.8 104 52 104 23.3 80.7 0 52 0z" fill="{ROJO}"/>'
        '<text x="52" y="72" text-anchor="middle" font-family="system-ui,sans-serif" '
        f'font-size="62" font-weight="800" fill="{BLANCO}">U</text></svg>'
    )


# Los selectores son `data-testid`, estables entre versiones de Streamlit, y
# no las clases `st-emotion-cache-…`, que cambian en cada una.
CSS = f"""
<style>
  [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {NAVY}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stSidebarContent"] {{ background: {NAVY_CLARO}; }}
  .stMainBlockContainer {{ max-width: 460px; padding-top: 1.2rem; }}

  /* Tarjetas blancas (la conversación, la ficha del destino).

     Streamlit no le pone un `data-testid` propio al contenedor con borde, así
     que el componente deja dentro una marca (`marca_tarjeta()`) y aquí se
     pinta el bloque que la contiene. Es el mismo truco de las burbujas: no
     depender de las clases internas.

     La ruta de hijos directos importa: sin ella, `:has()` calza también los
     bloques que envuelven a la tarjeta y termina pintada la página entera. */
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) {{
      background: {BLANCO};
      border: none;
      border-radius: 16px;
      padding: 10px 12px;
  }}
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) p,
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) li,
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) h1,
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) h2,
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] .ub-tarjeta) h3 {{
      color: {NAVY};
  }}

  /* Campos de texto: pastilla blanca. */
  [data-testid="stTextInputRootElement"] {{
      background: {BLANCO};
      border: none !important;
      border-radius: 999px;
      padding: 2px 12px;
  }}
  [data-testid="stTextInputField"] {{ background: {BLANCO}; color: {NAVY}; }}
  [data-testid="stTextInputField"]::placeholder {{ color: {GRIS_TEXTO}; }}
  [data-testid="stTextInputRootElement"] button {{ color: {NAVY}; }}

  /* Campo de destino: es un selectbox (da sugerencias al escribir), y tiene
     que verse igual que los demás campos. */
  [data-testid="stSelectbox"] [role="group"] {{
      background-color: {BLANCO} !important;
      border: none !important;
      border-radius: 999px;
      padding: 2px 8px 2px 14px;
  }}
  [data-testid="stSelectbox"] input {{
      background-color: {BLANCO} !important;
      color: {NAVY} !important;
  }}
  [data-testid="stSelectbox"] input::placeholder {{ color: {GRIS_TEXTO} !important; }}
  [data-testid="stSelectbox"] svg {{ fill: {NAVY}; color: {NAVY}; }}

  /* Caja de escritura del chat, también pastilla. */
  [data-testid="stChatInput"],
  [data-testid="stChatInput"] > div {{
      background: {BLANCO} !important;
      border: none !important;
      border-radius: 999px;
  }}
  [data-testid="stChatInputTextArea"] {{ background: {BLANCO} !important; color: {NAVY}; }}
  [data-testid="stChatInput"] textarea {{ color: {NAVY}; }}
  [data-testid="stChatInput"] textarea::placeholder {{ color: {GRIS_TEXTO}; }}
  [data-testid="stChatInputSubmitButton"] {{ color: {AZUL_MEDIO}; }}

  /* Botones: principal rojo, secundario azul apagado, ambos pastilla. */
  [data-testid="stBaseButton-primary"],
  [data-testid="stBaseButton-primaryFormSubmit"] {{
      /* `background-color` y no `background`: el atajo con !important borra la
         imagen de fondo de la mascota (ACT-014). */
      background-color: {ROJO} !important;
      color: {BLANCO} !important;
      border: none !important;
      border-radius: 999px;
      font-weight: 800;
      letter-spacing: .05em;
  }}
  [data-testid="stBaseButton-primary"]:hover,
  [data-testid="stBaseButton-primaryFormSubmit"]:hover {{
      background-color: {ROJO_OSCURO} !important;
  }}
  [data-testid="stBaseButton-secondary"],
  [data-testid="stBaseButton-secondaryFormSubmit"] {{
      background-color: {AZUL_MEDIO} !important;
      color: {NAVY} !important;
      border: none !important;
      border-radius: 999px;
      font-weight: 700;
  }}
  [data-testid="stBaseButton-secondary"]:hover,
  [data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
      background-color: {AZUL_CLARO} !important;
      color: {NAVY} !important;
  }}

  /* Conversación: el asistente en azul, quien pregunta en gris. */
  [data-testid="stChatMessage"] {{
      border-radius: 14px;
      padding: 10px 14px;
      margin-bottom: 8px;
  }}
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) {{ background: {AZUL_BURBUJA}; }}
  /* `!important` a propósito: la burbuja vive dentro de la tarjeta blanca, y
     la regla de la tarjeta pinta todos sus párrafos de azul oscuro. Sin esto,
     el texto del asistente quedaba azul sobre azul (1,9:1 de contraste: fue
     exactamente lo que el equipo reportó como "no se notan las letras"). */
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) p,
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) li,
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) strong {{
      color: {BLANCO} !important;
  }}
  /* Los enlaces salían en celeste sobre azul: ilegibles. Blanco subrayado. */
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) a {{
      color: {BLANCO} !important;
      text-decoration: underline;
  }}
  /* "De dónde saqué esto" dentro de la burbuja. */
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) [data-testid="stExpander"] details {{
      background: rgba(255,255,255,.12);
      border: none;
      border-radius: 10px;
  }}
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) [data-testid="stExpander"] summary,
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) [data-testid="stExpander"] p,
  [data-testid="stChatMessage"]:has(.ub-rol-assistant) [data-testid="stExpander"] svg {{
      color: {BLANCO} !important;
      fill: {BLANCO};
  }}
  [data-testid="stChatMessage"]:has(.ub-rol-user) {{ background: {GRIS_BURBUJA}; }}
  [data-testid="stChatMessage"]:has(.ub-rol-user) p {{ color: {NAVY}; }}

  /* Selector de vista (Preguntar / Mapa): el activo, rojo lleno. */
  [data-testid="stButtonGroup"] button {{
      border-radius: 999px !important;
      border: none !important;
      color: {BLANCO} !important;
      background: {NAVY_CLARO} !important;
      font-weight: 700;
  }}
  [data-testid="stButtonGroup"] button[aria-pressed="true"],
  [data-testid="stButtonGroup"] button[aria-checked="true"] {{
      background: {ROJO} !important;
      color: {BLANCO} !important;
  }}
  [data-testid="stButtonGroup"] button[aria-pressed="true"] p,
  [data-testid="stButtonGroup"] button[aria-checked="true"] p {{ color: {BLANCO} !important; }}

  /* Botón para abrir el chat: la mascota adentro, a la izquierda del texto.
     El CSS que la pinta se agrega aparte (`css_mascota`), solo si el archivo
     existe; sin él, el botón se ve igual pero sin la imagen. */
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]
      > [data-testid="stMarkdown"] .ub-marca-mascota) [data-testid="stBaseButton-primary"] {{
      padding: 12px 18px 12px 52px;
      background-position: 14px center;
      background-repeat: no-repeat;
      background-size: 30px 30px;
      text-align: center;
      text-transform: uppercase;
      font-size: .82rem;
      letter-spacing: .08em;
      box-shadow: 0 3px 0 {ROJO_OSCURO};
  }}
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]
      > [data-testid="stMarkdown"] .ub-marca-mascota)
      [data-testid="stBaseButton-primary"]:active {{
      transform: translateY(2px);
      box-shadow: 0 1px 0 {ROJO_OSCURO};
  }}

  /* Volver al mapa: un enlace, no un botón que compita con el resto. */
  [data-testid="stBaseButton-secondary"]:has(p:first-child) {{ font-weight: 700; }}

  /* Pantallas de carga (portada y bienvenida).

     Van como capa fija encima de todo y se desvanecen solas con una
     animación. No se usa `time.sleep`: bloquearía la sesión y, peor, dejaría
     la pantalla anterior asomándose en gris por debajo durante la espera
     (Streamlit mantiene a la vista lo de la pasada anterior hasta que la nueva
     termina). Así la aplicación carga por detrás mientras se ve la portada. */
  .ub-carga {{
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: {NAVY};
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 14px;
      text-align: center;
      animation: ub-desvanecer 1.9s ease-in forwards;
  }}
  @keyframes ub-desvanecer {{
      0%, 62% {{ opacity: 1; }}
      100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
  }}
  .ub-carga-titulo {{
      color: {BLANCO};
      font-weight: 800;
      letter-spacing: .12em;
      font-size: 1.7rem;
  }}
  .ub-carga-titulo span {{ color: {ROJO}; }}
  .ub-carga img {{ width: 190px; height: auto; }}

  /* Cabecera de la aplicación. */
  .ub-cabecera {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin: 0 0 2px;
  }}
  .ub-marca {{
      color: {BLANCO};
      font-weight: 800;
      letter-spacing: .04em;
      font-size: 1.5rem;
  }}
  .ub-marca span {{ color: {ROJO}; }}
  .ub-bajada {{
      color: {AZUL_MEDIO};
      text-align: center;
      font-size: .85rem;
      margin-bottom: 10px;
  }}
</style>
"""


# --- Mascota ---------------------------------------------------------------
# Los archivos los entrega el equipo y viven en assets/. Si no están, la
# aplicación funciona igual: cae al emoji. Así nadie queda bloqueado esperando
# una imagen, y el día que se copie el archivo aparece sola.
MASCOTA_CARA = "mascota.png"
MASCOTA_CUERPO = "mascota_cuerpo.png"
EMOJI_ASISTENTE = "🧭"


@lru_cache(maxsize=8)
def _imagen_uri(ruta: str, mtime: float) -> str:
    del mtime
    datos = base64.b64encode(Path(ruta).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{datos}"


def mascota(dir_assets: Path, archivo: str = MASCOTA_CARA) -> str | None:
    """La mascota como data URI, o None si el archivo todavía no está."""
    ruta = dir_assets / archivo
    if not ruta.exists():
        return None
    return _imagen_uri(str(ruta), ruta.stat().st_mtime)


# Silueta blanca para quien pregunta. Es un ícono genérico de interfaz, no
# arte del equipo, así que se dibuja acá y no se pide como archivo.
_AVATAR_USUARIO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">'
    f'<circle cx="20" cy="20" r="20" fill="{AZUL_BURBUJA}"/>'
    f'<circle cx="20" cy="15.5" r="6.4" fill="{BLANCO}"/>'
    f'<path d="M7.5 34.5c1.7-6.6 6.6-9.7 12.5-9.7s10.8 3.1 12.5 9.7z" fill="{BLANCO}"/>'
    "</svg>"
)


def avatar_usuario() -> str:
    """Silueta blanca de quien pregunta, como data URI."""
    datos = base64.b64encode(_AVATAR_USUARIO_SVG.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{datos}"


def avatar_asistente(dir_assets: Path) -> str:
    """Qué mostrar como avatar del asistente: la mascota si está, si no el emoji."""
    ruta = dir_assets / MASCOTA_CARA
    return str(ruta) if ruta.exists() else EMOJI_ASISTENTE


def css_mascota(dir_assets: Path) -> str:
    """CSS que mete la mascota dentro del botón de abrir el chat.

    Se genera aparte del CSS general porque lleva la imagen incrustada y solo
    tiene sentido si el archivo existe.
    """
    uri = mascota(dir_assets)
    if uri is None:
        return ""
    return (
        "<style>"
        '[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]'
        ' > [data-testid="stMarkdown"] .ub-marca-mascota)'
        ' [data-testid="stBaseButton-primary"]'
        f"{{background-image:url('{uri}') !important;}}"
        "</style>"
    )


def portada() -> str:
    """Pantalla de carga con la chincheta y el nombre (maqueta, lámina 2)."""
    return (
        f'<div class="ub-carga">{chincheta(120)}'
        '<div class="ub-carga-titulo"><span>U</span>-BÍCATE</div></div>'
    )


def bienvenida(dir_assets: Path) -> str:
    """Pantalla de bienvenida con la mascota (maqueta, lámina 6).

    Si el archivo de la mascota todavía no está, se muestra igual con la
    chincheta: la pantalla no depende de una imagen que puede faltar.
    """
    uri = mascota(dir_assets, MASCOTA_CUERPO)
    figura = f'<img src="{uri}" alt="Mascota de U-bícate">' if uri else chincheta(110)
    return (
        '<div class="ub-carga">'
        '<div class="ub-carga-titulo">¡BIENVENIDO!</div>'
        f"{figura}</div>"
    )


def marca_mascota() -> str:
    """Marca para que el CSS ponga la mascota dentro del botón que la sigue."""
    return '<span class="ub-marca-mascota"></span>'


def marca_tarjeta() -> str:
    """Marca invisible que convierte un contenedor en tarjeta blanca."""
    return '<span class="ub-tarjeta"></span>'


def cabecera() -> str:
    """Chincheta y nombre, como en la maqueta."""
    return (
        f'<div class="ub-cabecera">{chincheta(52)}'
        f'<div class="ub-marca"><span>U</span>-BÍCATE</div></div>'
    )
