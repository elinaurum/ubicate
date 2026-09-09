# Arquitectura

## Panorama

U-bícate es una aplicación web de una sola página, pensada para el teléfono. Un
selector arriba alterna entre dos vistas a pantalla completa: **Preguntar** (el
chat) y **Mapa** (buscador y plano). Cuando el asistente identifica un lugar, la
aplicación cambia sola a la vista del mapa (ver ADR-0006). Detrás hay cuatro
capas con dependencias en una sola dirección.

```
┌─────────────────────────────────────────────────────────────┐
│  ui/            Streamlit: componentes, estado de sesión,   │
│                 recursos cacheados, límites de uso          │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
┌───────────────▼──────────────┐  ┌───────────▼───────────────┐
│  chat/                       │  │  mapa/                    │
│  conocimiento (BM25)         │  │  render → HTML de folium  │
│  prompts · proveedores       │  │                           │
│  motor (orquestación)        │  │                           │
└───────────────┬──────────────┘  └───────────┬───────────────┘
                │                             │
┌───────────────▼─────────────────────────────▼───────────────┐
│  datos/repositorio        busqueda/ (normalización, índice)  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  modelos.py (pydantic)              config.py (entorno)      │
└──────────────────────────────────────────────────────────────┘
```

Regla: **nada bajo `ui/` importa Streamlit**. Es lo que permite probar el motor,
la búsqueda y el mapa sin levantar la aplicación, y es la diferencia práctica con
el prototipo, donde la lógica y la interfaz estaban entrelazadas en un archivo.

## Recorrido de una consulta al chat

```
"¿dónde queda la sala B04?"
   │
   ├─► conocimiento.buscar()    BM25 sobre 299 fragmentos → 6 más pertinentes
   ├─► repositorio.buscar()     coincidencia directa en el plano → B04
   │
   ├─► prompts.construir_sistema()
   │      identidad + reglas + catálogo de lugares + contexto recuperado
   │
   ├─► proveedor.responder()    anthropic / openai / eco
   │
   └─► motor._extraer_lugar()   detecta [[LUGAR:B04]], lo borra del texto
          │
          ├─► panel de chat     muestra la respuesta y sus fuentes
          └─► estado de sesión  fija el destino y cambia la vista a "mapa" →
                                el plano se abre con el marcador puesto
```

La marca `[[LUGAR:ID]]` es el contrato entre el modelo y la aplicación: obliga al
modelo a devolver la ubicación como **dato estructurado** además de como texto.
Eso es lo que faltaba para cerrar el Objetivo 3 de la documentación original.

## Recorrido de una búsqueda en el mapa

```
"b-04"  →  normalización → clave "b04"
        →  índice invertido
             ├─ una coincidencia   → destino fijado
             ├─ varias             → la interfaz pregunta cuál
             ├─ ninguna, pero hay parecidas (difflib) → "¿quisiste decir…?"
             └─ nada               → aviso y registro de la consulta fallida
```

El estado explícito es deliberado: el prototipo devolvía `None` y no distinguía
"no existe" de "hay varias opciones", así que fallaba en silencio.

## Decisiones de escala

Con ~2.000 personas y picos al inicio de cada bloque de clases, lo que importa no
es la velocidad del código sino qué se hace una vez y qué se hace por usuario.

| Recurso | Alcance | Mecanismo |
|---|---|---|
| Repositorio del campus | Una vez por proceso | `@st.cache_resource` |
| Base de conocimiento | Una vez por proceso | `@st.cache_resource` |
| Motor y proveedor | Una vez por proceso | `@st.cache_resource` |
| HTML del mapa | Por combinación destino × origen | `@st.cache_data(ttl=1h)` |
| Conversación e historial | Por sesión | `st.session_state` |

El plano en base64 pesa unos 120 KB. Regenerarlo en cada interacción de cada
usuario era el principal costo evitable de la vista; con caché, las
combinaciones frecuentes (las salas más buscadas) se sirven ya construidas.

Detalles de dimensionamiento y despliegue en [DESPLIEGUE.md](DESPLIEGUE.md).

## Por qué BM25 y no embeddings

La base son ~67.000 caracteres. Un índice vectorial agregaría una dependencia
pesada, un costo por consulta y un servicio más que mantener, a cambio de una
mejora marginal en un corpus de este tamaño. BM25 en Python puro se ejecuta en
milisegundos, no cuesta nada y es depurable a mano. Si la base crece un orden de
magnitud — por ejemplo al integrar U-Campus — corresponde reevaluarlo, y para eso
está el ADR-0003.

## Extensiones previstas

El diseño deja los puntos de enganche listos para lo que la documentación
original dejó planificado:

* **U-Campus.** El enrutamiento híbrido (consulta académica → base estructurada;
  consulta general → recuperación documental) encaja en `chat/motor.py` como una
  rama antes de armar el contexto. El campo `acceso` y el catálogo de lugares
  mapeables ya permiten enlazar sala → marcador automáticamente.
* **Geolocalización.** `repositorio.ruta(destino, origen_id)` ya acepta un origen
  arbitrario; hoy lo alimenta el selector del panel del mapa y mañana lo puede
  alimentar el GPS o el posicionamiento por WiFi.
* **Ruteo interior.** `Ruta` guarda una tupla de puntos, no dos: un camino con
  vértices intermedios no cambia el modelo ni el renderizador.
