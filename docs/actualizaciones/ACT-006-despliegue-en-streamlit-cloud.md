# ACT-006 — Preparar el despliegue del prototipo en Streamlit Community Cloud

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.4.1 |
| Tipo | infraestructura |
| Autor | Claude Code |
| Revisado por | |

## Qué se pidió

> ¿Dónde puedo desplegar este prototipo para que lo puedan ver más personas?
> Quiero subirlo con el modelo que usa la API (no el modo eco).

## Qué se hizo

- `requirements.txt` — se agrega `openai>=1.30` (estaba comentado). El proveedor
  configurado es Gemini, que usa el cliente de OpenAI contra su endpoint
  compatible (ADR-0005); sin el paquete, la aplicación caía a modo eco en
  silencio. Streamlit Cloud instala solo desde `requirements.txt`.
- `docs/DESPLIEGUE.md` — nueva sección 8: pasos para desplegar el prototipo en
  Streamlit Community Cloud, con la configuración de secretos, las limitaciones
  (sistema de archivos efímero, la app se duerme, cupo de la capa gratuita) y su
  lista de verificación.
- `pyproject.toml`, `src/ubicate/__init__.py` — versión 1.4.0 → 1.4.1.

## Por qué así

Streamlit Community Cloud es gratis, es de los mismos que hacen Streamlit y
maneja los WebSockets solo (el error de despliegue más común, `DESPLIEGUE.md`
§4). Vercel se descartó: es para sitios estáticos y funciones serverless, no
para un servidor Streamlit con WebSockets. Hugging Face Spaces queda como
alternativa si el prototipo supera 1 GB de RAM o se quiere usar el `Dockerfile`.

Se mantiene el proveedor Gemini que ya estaba en `.env`, para que la versión
pública responda con modelo de lenguaje y no en modo eco.

## Cómo se probó

- `ruff check` y `pytest` (38 pruebas) en verde con un entorno limpio.
- `python scripts/validar_datos.py` sin errores.
- El despliegue en sí lo hace el equipo desde <https://share.streamlit.io> con
  su cuenta de GitHub; los pasos y la prueba de humo están en `DESPLIEGUE.md` §8.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. `openai` ya estaba disponible como extra en `pyproject.toml` y en el entorno de desarrollo. |
| ¿Cambia el esquema de `data/`? | No. |
| ¿Requiere variables de entorno nuevas? | No nuevas. En Streamlit Cloud se cargan como "secrets" las mismas `UBICATE_*` del `.env`. |
| ¿Requiere migración? | No. |

## Al desplegar

1. Confirmar en GitHub Desktop que `.env` no está en los cambios.
2. *Commit* y *push* a `main`.
3. Seguir `docs/DESPLIEGUE.md` §8 para crear la app en Streamlit Cloud y cargar
   los secretos.

## Qué quedó pendiente

- El registro de consultas (`var/logs/consultas.jsonl`) no persiste en Streamlit
  Cloud. Si se quiere medir uso real antes de decidir la infraestructura
  definitiva, hay que enviarlo a un destino externo o adelantar el despliegue de
  las secciones 1–7.
- Fijar versiones exactas (`requirements.lock`, `DESPLIEGUE.md` §2) antes de
  cualquier uso serio; hoy `requirements.txt` usa rangos.
