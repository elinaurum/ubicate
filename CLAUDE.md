# Instrucciones para Claude

Este archivo se lee automáticamente al iniciar Claude Code en este repositorio.
Define cómo trabajar en U-bícate. Si algo aquí contradice una costumbre general,
manda lo que dice aquí.

---

## 1. Qué es este proyecto

U-bícate: asistente de orientación del campus Beauchef de la FCFM, Universidad de
Chile. Chatbot + mapa interactivo. Aplicación Streamlit en Python.

**Va a ser usado por estudiantes reales de la facultad (~2.000 personas).** No es
un ejercicio. Un dato equivocado hace que alguien llegue tarde a una prueba.

## 2. Con quién estás hablando

El equipo **no tiene formación en programación**. Esto cambia cómo respondes:

- Explica en español simple. Nada de jerga sin traducir.
- Cuando pidas ejecutar algo, entrega el comando exacto, listo para copiar, y di
  qué debería aparecer si funcionó.
- No des a elegir entre alternativas técnicas que no pueden evaluar. Elige tú,
  aplica, y explica en una frase por qué.
- Si algo que piden es mala idea, dilo directo y propón la alternativa. No lo
  hagas en silencio ni lo hagas igual.
- Al terminar, di siempre **cómo comprobar** que quedó bien.

## 3. Reglas que no se rompen

### 3.1 No inventar información de la facultad

Es la regla central del proyecto. Si no sabes en qué piso está una sala, cuánto
cuesta el casino o quién dirige una unidad, **no lo escribas**. Ni en `data/`, ni
en `data/kb/`, ni en un ejemplo.

Cuando falte un dato: anótalo en `docs/DEUDA_DATOS.md` con qué hay que verificar
y dónde. Un dato ausente es un problema menor; un dato inventado con seguridad
destruye la credibilidad de toda la herramienta.

Lo mismo aplica a las coordenadas del mapa: si no la puedes derivar del plano, no
la aproximes.

### 3.2 Cada cambio se documenta

Ningún cambio queda sin rastro. Después de tocar código o datos:

1. **Nota de actualización.** Copia `docs/actualizaciones/PLANTILLA.md` a
   `docs/actualizaciones/ACT-NNN-descripcion.md`. Numeración correlativa; mira
   cuál es el último para saber el siguiente.
2. **CHANGELOG.md.** Entrada bajo la versión, en Agregado / Cambiado / Corregido
   / Seguridad, enlazando la nota.
3. **ADR** en `docs/decisiones/` solo si la decisión condiciona el futuro (elegir
   una tecnología, cambiar el modelo de datos, cambiar cómo se despliega). Un ADR
   aceptado no se edita: se supera con otro.
4. **Documentación afectada.** Si cambió el esquema de datos → `docs/DATOS.md`.
   Si cambió el despliegue → `docs/DESPLIEGUE.md`.

Versionado semántico: MAYOR si cambia el esquema de `data/` o rompe la
configuración, MENOR si es funcionalidad nueva compatible, PARCHE si es
corrección. Sube `__version__` en `src/ubicate/__init__.py` cuando corresponda.

### 3.3 Verificar antes de entregar

Corre siempre, y no digas que está listo hasta que pasen:

```bash
make ci        # ruff + pytest + validación de datos
```

Si agregaste comportamiento, agrega su prueba. Si arreglaste un error, agrega la
prueba que lo habría detectado.

### 3.4 Nada de secretos

Jamás escribas una API key en el código, en un ejemplo, en un commit o en la
documentación. Las claves van en `.env`, que está en `.gitignore`.

## 4. Arquitectura: la regla estructural

Dependencias en una sola dirección:

```
ui/ → chat/ y mapa/ → datos/ y busqueda/ → modelos.py y config.py
```

**Ningún módulo fuera de `src/ubicate/ui/` puede importar `streamlit`.** Es lo que
permite que las pruebas corran en menos de un segundo sin levantar la aplicación.
Si te ves tentado a importar Streamlit en el dominio para mostrar un aviso: no.
Devuelve un valor y que la capa de interfaz decida qué mostrar.

Ninguna cadena de configuración escrita a mano en el código: va en `config.py` y
se lee de variables de entorno con prefijo `UBICATE_`.

## 5. Mapa del repositorio

| Ruta | Qué hay | Cuidado |
|---|---|---|
| `src/ubicate/modelos.py` | Modelos de dominio (pydantic) | Cambiarlos puede invalidar `data/` |
| `src/ubicate/config.py` | Toda la parametrización | |
| `src/ubicate/busqueda/` | Normalización de texto e índice | |
| `src/ubicate/datos/repositorio.py` | Carga, validación y consultas del campus | |
| `src/ubicate/mapa/render.py` | Mapa folium → HTML | Escapa siempre lo que venga de datos |
| `src/ubicate/chat/prompts.py` | Prompt del asistente | Cambiarlo es cambio de producto: sube `VERSION_PROMPT` |
| `src/ubicate/chat/conocimiento.py` | Recuperación BM25 | |
| `src/ubicate/chat/motor.py` | Orquestación del chat | |
| `src/ubicate/ui/` | Streamlit | Único lugar donde se importa streamlit |
| `data/*.json` | Edificios y salas | Esquema en `docs/DATOS.md` |
| `data/kb/*.md` | Base de conocimiento | Cada archivo lleva cabecera con fuente y vigencia |
| `scripts/_*.json`, `scripts/_kb_origen.md` | Insumos históricos de la migración | No son fuente de verdad; no los edites |

## 6. Comandos

```bash
make app        # levantar la aplicación
make test       # pruebas
make lint       # estilo
make validar    # integridad de datos y base de conocimiento
make probar     # diagnosticar la conexión con el proveedor de modelo
make ci         # lint + test + validar
```

## 7. Contexto ya decidido — no lo redescubras

Antes de proponer un cambio estructural, lee `docs/decisiones/`. Ya está resuelto
y con sus razones:

- **ADR-0001** — arquitectura por capas, dominio separado de Streamlit.
- **ADR-0002** — el chat marca el destino con `[[LUGAR:ID]]`, no con detección de
  nombres ni tool use.
- **ADR-0003** — recuperación BM25 en Python puro, sin embeddings ni base
  vectorial.
- **ADR-0004** — el mapa se renderiza como HTML cacheado, sin `streamlit-folium`.
- **ADR-0005** — un solo cliente para todos los endpoints compatibles con OpenAI.

Si crees que uno está equivocado, dilo y argumenta. No lo cambies en silencio.

`docs/ROADMAP.md` tiene lo planificado y no implementado, con su diseño:
integración con U-Campus, mapa 3D con ruteo interior, geolocalización.

## 8. Sensibilidades del dominio

- **Localización de docentes.** Se presenta siempre como "según su horario de
  docencia publicado debería estar en la sala X", nunca como ubicación en tiempo
  real de una persona, y priorizando los canales formales de contacto. Lo primero
  es información académica pública; lo segundo sería seguimiento de personas.
- **Datos de contacto.** Solo los ya públicos en directorios institucionales.
- **Consultas de bienestar y salud mental.** Derivar a las unidades de apoyo con
  sus datos, en tono cuidadoso, sin diagnosticar.
- **Métricas.** No agregar nada que permita identificar a una persona. Ver
  `docs/PRIVACIDAD.md`.
- **Accesibilidad.** Cuando se implemente ruteo, la ruta que evita escaleras es
  requisito desde la primera versión, no un extra. El campus tiene trece niveles.

## 9. Cómo trabajar un pedido

1. Lee lo que ya existe antes de escribir. Es probable que el punto de enganche
   esté puesto.
2. Si el pedido es ambiguo o hay una decisión de producto de por medio, pregunta
   antes de asumir.
3. Cambios acotados. Es preferible entregar algo pequeño que funciona y está
   documentado, a algo grande a medio terminar.
4. Corre `make ci`.
5. Escribe la nota y el CHANGELOG.
6. Cierra diciendo qué cambió, cómo probarlo a mano, y qué quedó pendiente.
