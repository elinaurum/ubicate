"""Pantalla de acceso: la puerta temporal mientras no hay cuentas.

Ver ADR-0010. La clave decide qué versión se muestra —estable o en
desarrollo—, no quién entra: no hay cuentas, no se guarda nada de quien accede
y no se registra ningún intento (`docs/PRIVACIDAD.md`).

El diseño (fondo azul noche, botón rojo, campos blancos redondeados) sigue la
maqueta que entregó el equipo. Los colores viven en constantes aquí y no
repartidos por el CSS, para poder cambiarlos en un solo lugar.
"""

from __future__ import annotations

import streamlit as st

from ubicate.acceso import rol_para
from ubicate.ui import estado, recursos

FONDO = "#2C3E5C"
ROJO = "#E63329"
ROJO_OSCURO = "#C42A21"
AZUL_SECUNDARIO = "#7391B5"
BLANCO = "#FFFFFF"
GRIS_TEXTO = "#9AA5B1"

# Chincheta con la U, el mismo símbolo de la maqueta. Va como SVG en línea:
# no agrega un archivo que cargar ni una petición más.
LOGO = f"""
<div style="display:flex;justify-content:center;margin:8px 0 4px">
  <svg width="104" height="124" viewBox="0 0 104 124" fill="none"
       xmlns="http://www.w3.org/2000/svg" role="img" aria-label="U-bícate">
    <path d="M52 0C23.3 0 0 23.3 0 52c0 31.8 41.6 66.9 48.3 72.3a5.9 5.9 0
             0 0 7.4 0C62.4 118.9 104 83.8 104 52 104 23.3 80.7 0 52 0z"
          fill="{ROJO}"/>
    <text x="52" y="72" text-anchor="middle" font-family="system-ui,sans-serif"
          font-size="62" font-weight="800" fill="{BLANCO}">U</text>
  </svg>
</div>
"""

CSS = f"""
<style>
  [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
      background: {FONDO};
  }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{
      display: none;
  }}
  [data-testid="stAppViewContainer"] .stMainBlockContainer {{
      max-width: 420px;
      padding-top: 2.2rem;
  }}

  /* Campos: pastilla blanca, sin borde, como en la maqueta.
     Los selectores son `data-testid`, no las clases de emotion
     (`st-emotion-cache-…`), que cambian con cada versión de Streamlit. */
  [data-testid="stTextInputRootElement"] {{
      background: {BLANCO};
      border: none !important;
      border-radius: 999px;
      padding: 4px 12px;
      box-shadow: none;
  }}
  [data-testid="stTextInputField"] {{
      background: {BLANCO};
      color: {FONDO};
      font-size: 1rem;
      padding: 10px 8px;
  }}
  [data-testid="stTextInputField"]::placeholder {{ color: {GRIS_TEXTO}; }}
  [data-testid="stTextInputRootElement"] button {{ color: {FONDO}; }}

  /* Botón principal (el de un formulario es su propio testid): rojo, pastilla. */
  [data-testid="stBaseButton-primaryFormSubmit"],
  [data-testid="stBaseButton-primary"] {{
      background: {ROJO} !important;
      color: {BLANCO} !important;
      border: none !important;
      border-radius: 999px;
      font-weight: 800;
      letter-spacing: .06em;
      padding: 12px 0;
  }}
  [data-testid="stBaseButton-primaryFormSubmit"]:hover,
  [data-testid="stBaseButton-primary"]:hover {{
      background: {ROJO_OSCURO} !important;
  }}

  /* Botón secundario: azul apagado con texto oscuro. */
  [data-testid="stBaseButton-secondary"] {{
      background: {AZUL_SECUNDARIO} !important;
      color: {FONDO} !important;
      border: none !important;
      border-radius: 999px;
      font-weight: 800;
      letter-spacing: .06em;
      padding: 10px 0;
  }}
  [data-testid="stBaseButton-secondary"]:hover {{
      background: #8AA5C4 !important;
      color: {FONDO} !important;
  }}

  .ub-titulo {{
      color: {BLANCO};
      text-align: center;
      font-weight: 800;
      letter-spacing: .08em;
      font-size: 1.45rem;
      margin: 2px 0 14px;
  }}
  .ub-enlace {{
      color: {BLANCO};
      text-align: center;
      font-size: .92rem;
      text-decoration: underline;
      margin: 2px 0 10px;
  }}
  .ub-pie {{
      color: {BLANCO};
      text-align: center;
      font-weight: 700;
      font-size: .95rem;
      margin: 26px 0 6px;
  }}
  .ub-nota {{
      color: {AZUL_SECUNDARIO};
      text-align: center;
      font-size: .78rem;
      margin-top: 22px;
      line-height: 1.5;
  }}
</style>
"""


def _aviso_sin_cuentas() -> None:
    st.info(
        "Todavía no hay cuentas: el acceso es con la clave que entrega el "
        "equipo. Si no la tienes o no te funciona, escríbenos."
    )


def render() -> None:
    """Dibuja la pantalla y, si la clave es correcta, deja pasar."""
    settings = recursos.settings()

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(LOGO, unsafe_allow_html=True)
    st.markdown('<div class="ub-titulo">INICIAR SESIÓN</div>', unsafe_allow_html=True)

    with st.form("ub_acceso", border=False):
        st.text_input(
            "Correo electrónico",
            key="ub_correo",
            placeholder="Correo electrónico",
            label_visibility="collapsed",
        )
        clave = st.text_input(
            "Contraseña",
            key="ub_clave",
            type="password",
            placeholder="Contraseña",
            label_visibility="collapsed",
        )
        st.markdown('<div class="ub-enlace">Olvidé la contraseña</div>', unsafe_allow_html=True)
        entrar = st.form_submit_button(
            "INICIAR SESIÓN", type="primary", use_container_width=True
        )

    if entrar:
        rol = rol_para(clave, settings)
        if rol is None:
            # Un solo mensaje para clave vacía o equivocada: decir cuál de las
            # dos falló le regalaría información a quien esté probando.
            st.error("Esa contraseña no es correcta.")
        else:
            estado.fijar_rol(rol)
            st.rerun()

    st.markdown('<div class="ub-pie">¿No tienes cuenta?</div>', unsafe_allow_html=True)
    if st.button("REGISTRARSE", use_container_width=True, type="secondary"):
        _aviso_sin_cuentas()

    st.markdown(
        '<div class="ub-nota">El correo todavía no se usa ni se guarda: '
        "esta pantalla solo separa la versión estable de la que está en "
        "construcción.</div>",
        unsafe_allow_html=True,
    )
