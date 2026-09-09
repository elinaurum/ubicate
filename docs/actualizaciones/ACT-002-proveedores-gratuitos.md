# ACT-002 — Habilitar proveedores de modelo con capa gratuita

| Campo | Valor |
|---|---|
| Fecha | 2026-09-08 |
| Versión | 1.1.0 |
| Tipo | funcionalidad |
| Autor | Equipo U-bícate |
| Revisado por | _pendiente_ |

## Qué se pidió

Poder trabajar con una API gratuita mientras el proyecto no tiene presupuesto, y
que el repositorio sirva para trabajar con más personas.

## Qué se hizo

- `src/ubicate/config.py` — proveedores nuevos `gemini`, `groq` y `compatible`;
  diccionario `BASE_URLS` con los endpoints; propiedad `base_url_efectiva`;
  `usa_llm` ahora exige `base_url` cuando el proveedor es `compatible`.
- `src/ubicate/chat/proveedores.py` — `ProveedorOpenAI` recibe la URL base de la
  configuración y reporta el nombre real del proveedor en las métricas.
- `.env.example` — recetas listas para Gemini, Groq, Anthropic, OpenAI y
  endpoints compatibles.
- `tests/test_proveedores.py` — cinco pruebas nuevas.
- `docs/decisiones/ADR-0005-proveedores-compatibles-openai.md`.

## Por qué así

Gemini y Groq exponen `/chat/completions` con el contrato de OpenAI, así que un
solo cliente atiende a los tres. Escribir una clase por proveedor habría sido
triplicar código idéntico. El razonamiento completo y sus límites están en el
[ADR-0005](../decisiones/ADR-0005-proveedores-compatibles-openai.md).

`anthropic` sigue con clase propia porque su API tiene otro contrato.

## Cómo se probó

- 35 pruebas en verde (5 nuevas), `ruff` sin observaciones, `make validar` limpio.
- Verificado que sin API key o sin `base_url` la aplicación degrada a modo eco en
  lugar de fallar.
- Verificado que la URL base explícita tiene prioridad sobre la preconfigurada,
  que es lo que permite pasar por un proxy.

> Pendiente: probar contra los endpoints reales de Gemini y Groq con una key.
> Las pruebas automatizadas cubren la selección y la degradación, no la llamada
> de red.

## Impacto

| Aspecto | Detalle |
|---|---|
| ¿Rompe algo existente? | No. Quien use `anthropic` u `openai` no cambia nada |
| ¿Cambia el esquema de `data/`? | No |
| ¿Requiere variables de entorno nuevas? | `UBICATE_BASE_URL`, opcional |
| ¿Requiere migración? | No |

## Al desplegar

1. `pip install openai` si se va a usar Gemini, Groq o un endpoint compatible.
2. Elegir la receta en `.env` y pegar la key.
3. Confirmar en la barra lateral que el modelo indicado no es "eco".

## Qué quedó pendiente

- Probar contra los endpoints reales con una key.
- Reintentos con espera ante error 429: las capas gratuitas devuelven ese código
  al pasarse de cuota y hoy la respuesta es un mensaje de error genérico.
- Reevaluar este diseño cuando se integre U-Campus, porque ahí conviene tool use
  y la compatibilidad entre proveedores deja de ser suficiente.
