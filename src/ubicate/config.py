"""Configuración central de U-bícate.

Toda la parametrización vive aquí y se alimenta de variables de entorno con el
prefijo ``UBICATE_`` (o de un archivo ``.env`` en la raíz del repositorio).
Ningún otro módulo debe leer ``os.environ`` directamente.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/ubicate/config.py -> src/ubicate -> src -> raíz del repositorio
RAIZ = Path(__file__).resolve().parents[2]


class Entorno(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCCION = "produccion"


class ProveedorLLM(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"          # vía endpoint compatible con OpenAI
    GROQ = "groq"              # vía endpoint compatible con OpenAI
    COMPATIBLE = "compatible"  # cualquier otro endpoint compatible: exige base_url
    ECO = "eco"                # sin LLM: recuperación directa sobre la base


# Endpoints compatibles con la API de OpenAI. Permiten usar un solo cliente
# para varios proveedores; ver docs/decisiones/ADR-0005.
BASE_URLS: dict[ProveedorLLM, str] = {
    ProveedorLLM.GEMINI: "https://generativelanguage.googleapis.com/v1beta/openai/",
    ProveedorLLM.GROQ: "https://api.groq.com/openai/v1",
}

# Proveedores que se atienden con el cliente de OpenAI.
COMPATIBLES_OPENAI = frozenset(
    {ProveedorLLM.OPENAI, ProveedorLLM.GEMINI, ProveedorLLM.GROQ, ProveedorLLM.COMPATIBLE}
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UBICATE_",
        env_file=RAIZ / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Entorno y observabilidad ---------------------------------------
    entorno: Entorno = Entorno.LOCAL
    log_nivel: str = "INFO"
    log_formato: str = Field(default="texto", pattern="^(texto|json)$")
    metricas_activas: bool = True

    # --- Rutas ------------------------------------------------------------
    dir_datos: Path = RAIZ / "data"
    dir_kb: Path = RAIZ / "data" / "kb"
    dir_assets: Path = RAIZ / "assets"
    dir_var: Path = RAIZ / "var"

    # --- Mapa -------------------------------------------------------------
    # Lienzo virtual sobre el que están expresadas las coordenadas de los
    # datos. NO es el tamaño en píxeles del PNG (ver docs/DATOS.md §3).
    lienzo_alto: int = 2756
    lienzo_ancho: int = 1500
    mapa_imagen: str = "mapa_beauchef.png"
    mapa_alto_px: int = 620

    # --- Búsqueda ---------------------------------------------------------
    umbral_difuso: float = Field(default=0.72, ge=0.0, le=1.0)
    max_sugerencias: int = Field(default=5, ge=1, le=20)

    # --- Chat -------------------------------------------------------------
    proveedor_llm: ProveedorLLM = ProveedorLLM.ECO
    modelo_llm: str = ""  # cada proveedor tiene sus nombres; ver .env.example
    api_key: str | None = None
    # Solo se necesita para proveedor "compatible"; gemini y groq lo traen fijo.
    base_url: str | None = None
    max_tokens: int = 700
    temperatura: float = Field(default=0.2, ge=0.0, le=1.0)
    historial_max_turnos: int = Field(default=8, ge=1, le=40)
    kb_fragmentos: int = Field(default=6, ge=1, le=20)

    # --- Límites de uso (protegen costo y disponibilidad) -----------------
    mensajes_por_sesion: int = Field(default=60, ge=1)
    segundos_entre_mensajes: float = Field(default=1.0, ge=0.0)

    @field_validator("log_nivel")
    @classmethod
    def _nivel_valido(cls, v: str) -> str:
        validos = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in validos:
            raise ValueError(f"log_nivel debe ser uno de {sorted(validos)}")
        return v

    # --- Derivados --------------------------------------------------------
    @property
    def ruta_edificios(self) -> Path:
        return self.dir_datos / "edificios.json"

    @property
    def ruta_salas(self) -> Path:
        return self.dir_datos / "salas.json"

    @property
    def ruta_imagen_mapa(self) -> Path:
        return self.dir_assets / self.mapa_imagen

    @property
    def ruta_metricas(self) -> Path:
        return self.dir_var / "logs" / "consultas.jsonl"

    @property
    def limites_lienzo(self) -> list[list[float]]:
        """Bounds en formato folium: [[y_min, x_min], [y_max, x_max]]."""
        return [[0.0, 0.0], [float(self.lienzo_alto), float(self.lienzo_ancho)]]

    @property
    def base_url_efectiva(self) -> str | None:
        """URL del endpoint: la explícita gana sobre la preconfigurada."""
        return self.base_url or BASE_URLS.get(self.proveedor_llm)

    @property
    def usa_llm(self) -> bool:
        if self.proveedor_llm is ProveedorLLM.ECO or not self.api_key:
            return False
        return not (
            self.proveedor_llm is ProveedorLLM.COMPATIBLE and not self.base_url_efectiva
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Instancia única de configuración (cacheada por proceso)."""
    return Settings()
