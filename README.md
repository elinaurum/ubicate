# U-bícate

Asistente de orientación e información para el campus Beauchef de la Facultad de
Ciencias Físicas y Matemáticas (FCFM), Universidad de Chile.

Combina un **chatbot** que responde sobre servicios, trámites, cursos y espacios
de la facultad, y un **mapa interactivo** del campus que muestra dónde queda cada
sala o edificio y cómo llegar desde el acceso correspondiente.

Equipo: Alexia Roa · Benjamín Zuñiga · Ignacio Arena

---

## Estado

Versión **1.2.1**. Reescritura del prototipo sobre una arquitectura por capas,
pensada para uso real de la comunidad de la facultad (~2.000 personas).

Lo que cambió respecto del prototipo está en el [CHANGELOG](CHANGELOG.md).

## Partir en tres minutos

```bash
git clone <repositorio> && cd ubicate
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
streamlit run app.py
```

Se abre en `http://localhost:8501`. Sin API key funciona en **modo eco**: responde
con los fragmentos de la base de conocimiento, sin modelo de lenguaje.

Para activar el chatbot completo, en `.env`:

```
UBICATE_PROVEEDOR_LLM=gemini
UBICATE_MODELO_LLM=gemini-3.6-flash
UBICATE_API_KEY=...
```

y `pip install openai`. Hay recetas para Gemini, Groq, Anthropic, OpenAI y
endpoints compatibles (Ollama, OpenRouter) en `.env.example`.

## Comandos

| Comando | Qué hace |
|---|---|
| `make app` | Levanta la aplicación |
| `make test` | Corre la suite de pruebas |
| `make lint` | Revisa estilo con ruff |
| `make validar` | Valida `data/` y la base de conocimiento |
| `make probar` | Diagnostica la conexión con el proveedor de modelo |
| `make ci` | Las tres anteriores, igual que en GitHub Actions |
| `make kb` | Regenera `data/kb/` desde el documento maestro |

## Estructura

```
ubicate/
├── app.py                      Lanzador (streamlit run app.py)
├── src/ubicate/
│   ├── config.py               Configuración por variables de entorno
│   ├── modelos.py              Modelos de dominio validados (pydantic)
│   ├── busqueda/               Normalización de texto e índice de búsqueda
│   ├── datos/repositorio.py    Carga, validación y consultas del campus
│   ├── mapa/render.py          Construcción del mapa (folium → HTML)
│   ├── chat/                   Conocimiento, prompts, proveedores, motor
│   ├── observabilidad/         Logging estructurado y métricas de uso
│   └── ui/                     Streamlit: estado, recursos y componentes
├── data/
│   ├── edificios.json          27 edificios y accesos
│   ├── salas.json              33 salas
│   └── kb/                     Base de conocimiento en Markdown con metadatos
├── assets/mapa_beauchef.png    Plano del campus
├── docs/                       Arquitectura, datos, despliegue, operación, ADR
├── scripts/                    Migración, importación de KB, validación
└── tests/                      30 pruebas automatizadas
```

## Documentación

| Documento | Para qué |
|---|---|
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Cómo está armado y por qué |
| [docs/DATOS.md](docs/DATOS.md) | Esquemas y cómo agregar una sala o un edificio |
| [docs/OPERACION.md](docs/OPERACION.md) | Régimen de actualización y respuesta a incidentes |
| [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md) | Puesta en producción y capacidad para 2.000 usuarios |
| [docs/PRIVACIDAD.md](docs/PRIVACIDAD.md) | Qué datos se registran y cuáles no |
| [docs/DEUDA_DATOS.md](docs/DEUDA_DATOS.md) | Inconsistencias detectadas pendientes de verificar en terreno |
| [docs/CONTRIBUIR.md](docs/CONTRIBUIR.md) | Cómo trabajar en el repositorio |
| [docs/GITHUB.md](docs/GITHUB.md) | Subir a GitHub y colaborar en equipo |
| [docs/decisiones/](docs/decisiones/) | Decisiones de arquitectura (ADR) |
| [docs/actualizaciones/](docs/actualizaciones/) | Una nota por cada cambio entregado |

## Licencia

MIT. Los contenidos de `data/kb/` provienen de canales institucionales públicos
de la FCFM y del levantamiento del equipo.
