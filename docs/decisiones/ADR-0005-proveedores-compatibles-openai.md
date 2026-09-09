# ADR-0005 · Un solo cliente para todos los endpoints compatibles con OpenAI

- **Estado:** aceptada
- **Fecha:** 2026-09-08

## Contexto

El proyecto necesita un modelo de lenguaje sin presupuesto asignado. Los
proveedores con capa gratuita útil (Google AI Studio, Groq) exponen su API con
el mismo contrato que OpenAI: `/chat/completions`, mismos campos, misma forma de
respuesta. Escribir una clase por proveedor sería triplicar código idéntico.

Además, en un proyecto universitario el proveedor va a cambiar: se acaba la
cuota, aparece un convenio de la facultad, alguien monta un modelo local. Eso no
debería obligar a tocar el código.

## Decisión

`ProveedorOpenAI` atiende a **todos** los endpoints compatibles. El proveedor
elegido determina la URL base:

| `UBICATE_PROVEEDOR_LLM` | URL base |
|---|---|
| `openai` | la de la librería |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `groq` | `https://api.groq.com/openai/v1` |
| `compatible` | la que se indique en `UBICATE_BASE_URL` |

`anthropic` queda aparte porque su API tiene otro contrato (el prompt de sistema
va en un parámetro propio, no como primer mensaje).

Cambiar de proveedor son dos líneas del `.env` y un reinicio.

## Consecuencias

**A favor**

- Un modelo local con Ollama, un proxy institucional o OpenRouter funcionan sin
  escribir código: `compatible` + `base_url`.
- Si un proveedor cambia sus condiciones —cosa que pasa seguido en las capas
  gratuitas— migrar es un cambio de configuración, no de código.

**En contra**

- La compatibilidad es del contrato básico. Las funciones propias de cada
  proveedor (tool use, caché de prompt, control de razonamiento) no están
  cubiertas. Cuando se integre U-Campus con llamada a función habrá que
  reevaluar este ADR y probablemente escribir un cliente por proveedor.
- Los mensajes de error llegan con el vocabulario de cada servicio, lo que hace
  el diagnóstico algo más confuso.

## Nota

Las capas gratuitas se agotan por **tokens por minuto** antes que por requests.
El prompt de U-bícate ronda los 1.400 tokens, así que un proveedor con 6.000
TPM soporta unas 3 consultas por minuto. Ver `docs/DESPLIEGUE.md` §1.
