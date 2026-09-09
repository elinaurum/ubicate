# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Versionado [SemVer](https://semver.org/lang/es/): `MAYOR.MENOR.PARCHE`.

Convención del proyecto:

* **MAYOR** — cambia el esquema de `data/` o rompe la configuración existente.
* **MENOR** — funcionalidad nueva compatible hacia atrás.
* **PARCHE** — corrección de errores, datos o contenidos.

Cada versión enlaza su nota de actualización en `docs/actualizaciones/`, donde
queda el detalle: qué se cambió, por qué, cómo se probó y qué hay que hacer al
desplegar.

---

## [1.4.0] — 2026-09-08

El chat deja de saltar solo al mapa: ofrece cada lugar como un botón y el
estudiante elige cuál abrir. Una consulta puede sugerir varios lugares.
Nota completa: [ACT-005](docs/actualizaciones/ACT-005-botones-de-lugar-en-el-chat.md).

### Cambiado

* Cuando el asistente identifica lugares, aparece **un botón "📍" por lugar**
  bajo la respuesta. El mapa se abre —y la vista cambia— solo al pulsarlo.
  Antes se fijaba un único lugar y se saltaba al mapa automáticamente.
* El asistente puede marcar **varios lugares** en una respuesta, no uno solo
  (`VERSION_PROMPT` 1.0.0 → 1.1.0).
* Las citas ("de dónde saqué esto") quedan guardadas por mensaje y se
  redibujan al recargar el historial, no solo en la última respuesta en vivo.
* [ADR-0007](docs/decisiones/ADR-0007-varios-lugares-con-botones.md) supera a
  ADR-0002 y revierte el salto automático de ACT-004.

### Interno

* `Respuesta.destino` → `Respuesta.destinos` (tupla); `destino` queda como
  propiedad (el primero) para las métricas.
* `Mensaje` gana `citas` y `lugares`; `Conversacion.agregar` los acepta como
  parámetros opcionales. `Destino.etiqueta_corta` para el texto de los botones.

---

## [1.3.0] — 2026-09-08

Interfaz reorganizada para uso en el teléfono, que es el contexto real: se
pregunta dónde queda algo mientras se camina, no sentado frente a un computador.
Nota completa: [ACT-004](docs/actualizaciones/ACT-004-interfaz-para-telefono.md).

### Cambiado

* El chat y el mapa ya no comparten pantalla. Un selector arriba ("Preguntar" /
  "Mapa") muestra uno a la vez, a pantalla completa. Layout centrado y barra
  lateral cerrada al entrar.
* El puente chat → mapa ahora **lleva** al usuario al plano cuando el asistente
  identifica un lugar, en vez de actualizar un mapa que quedaba fuera de pantalla.
* El selector "¿Dónde estás ahora?" pasa de la barra lateral al panel del mapa,
  junto al buscador.
* Piso de `streamlit` sube de 1.36 a 1.50 (`st.segmented_control`).
* [ADR-0006](docs/decisiones/ADR-0006-navegacion-una-vista-a-la-vez.md): por qué
  una vista a la vez y por qué no pestañas.

---

## [1.2.0] — 2026-09-08

Herramientas para diagnosticar por qué falla el chat.
Nota completa: [ACT-003](docs/actualizaciones/ACT-003-diagnostico-de-proveedor.md).

### Agregado

* `scripts/probar_proveedor.py` (`make probar`): diagnostica la conexión con el
  proveedor, traduce el error a una causa concreta y lista los modelos que la
  key tiene disponibles.
* Reintento con espera creciente ante errores de límite de velocidad (429).
* `CLAUDE.md`: instrucciones permanentes para trabajar con Claude Code.

### Cambiado

* Fuera de producción, la interfaz muestra el detalle técnico del error del
  proveedor bajo la respuesta. En producción se mantiene el mensaje genérico.

---

## [1.1.0] — 2026-09-08

Soporte para proveedores con capa gratuita, para poder trabajar sin presupuesto.
Nota completa: [ACT-002](docs/actualizaciones/ACT-002-proveedores-gratuitos.md).

### Agregado

* Proveedores `gemini` y `groq`, que usan sus endpoints compatibles con OpenAI y
  no requieren código propio.
* Proveedor `compatible` con `UBICATE_BASE_URL`, para modelos locales (Ollama),
  OpenRouter o un proxy institucional.
* Recetas de configuración listas para copiar en `.env.example`.
* [ADR-0005](docs/decisiones/ADR-0005-proveedores-compatibles-openai.md) y cinco
  pruebas de selección y degradación de proveedor.

### Cambiado

* `ProveedorOpenAI` toma su URL base de la configuración y reporta el nombre del
  proveedor real en las métricas, en vez de decir siempre "openai".
* `UBICATE_MODELO_LLM` queda vacío por defecto: cada proveedor tiene sus nombres
  de modelo y no hay un valor razonable para todos.

---

## [1.0.0] — 2026-09-08

Reescritura completa del prototipo sobre una arquitectura por capas, apuntando a
uso real de la facultad. Nota completa: [ACT-001](docs/actualizaciones/ACT-001-reestructuracion.md).

### Agregado

* Arquitectura por capas en `src/ubicate/`: dominio, datos, búsqueda, mapa, chat,
  observabilidad e interfaz, con dependencias en una sola dirección.
* Modelos de dominio validados con pydantic. Los JSON se validan al arrancar y la
  aplicación falla con un mensaje concreto en vez de reventar frente al usuario.
* Configuración centralizada por variables de entorno (`UBICATE_*`) con `.env`.
* Búsqueda tolerante: `B-04`, `b 04`, `sala B04` y `B04` resuelven al mismo
  destino. Desambiguación cuando hay varias coincidencias y sugerencias por
  similitud ante errores de tipeo.
* Base de conocimiento fragmentada en `data/kb/` con metadatos de fuente,
  fecha de actualización y vigencia, más recuperación BM25 por consulta.
* Puente automático chat → mapa: la respuesta del asistente enciende el marcador
  sin que el usuario copie el nombre al buscador. Cierra el Objetivo 3.
* Selección manual del punto de partida ("¿dónde estás ahora?"), el respaldo
  previsto en la sección 9.3 de la documentación mientras no haya geolocalización.
* Modo **eco**: la aplicación es plenamente usable sin API key ni modelo de
  lenguaje. Es el plan de continuidad si el proveedor falla o se agota el
  presupuesto.
* Registro de consultas en JSONL, incluyendo las que quedan sin responder, para
  priorizar el crecimiento de la base con datos y no con intuición.
* Límites por sesión de mensajes y frecuencia.
* Logging estructurado, con salida JSON opcional para producción.
* 30 pruebas automatizadas, linter y validación de datos en CI (GitHub Actions).
* `Dockerfile` con usuario sin privilegios y healthcheck.
* Documentación: arquitectura, datos, operación, despliegue, privacidad, deuda de
  datos, guía de contribución y cuatro ADR.

### Cambiado

* El origen de la ruta ya no se deduce del prefijo del id (`id.startswith("851_")`)
  sino de un campo explícito `acceso` en cada edificio.
* `piso` pasa de texto (`"-1"`) a entero, validado.
* Los alias dejan de enumerar variantes ortográficas: eso lo resuelve la
  normalización. Solo quedan los alias con significado propio.
* La imagen del plano se incrusta en base64. La ruta relativa
  `assets/mapa_beauchef.png` no resolvía dentro del iframe del mapa.
* El mapa se renderiza como HTML cacheado por combinación destino × origen, en
  vez de reconstruirse en cada interacción.

### Corregido

* **Plano en blanco.** El `ImageOverlay` apuntaba a una ruta relativa inaccesible
  desde el navegador.
* **Inyección de HTML.** Las descripciones e instrucciones de los JSON se
  insertaban sin escapar en los globos del mapa.
* **Alias corruptos.** Las salas `E111`, `E213`–`E216` tenían alias con comillas
  tipográficas dentro del string (`E-111”, “e 111`), que no coincidían con nada.
* **Alias ambiguo `auditorio`.** Apuntaba a la vez al Gorbea (850) y al d'Etigny
  (851); la última coincidencia ganaba en silencio. Ahora la interfaz pregunta.
* **Duplicado Gorbea.** `GORBEA_SALA` y `850_AUDITORIO` eran el mismo lugar en dos
  tablas, compitiendo por la misma clave de búsqueda. Se fusionaron en el edificio.
* **Búsqueda distingue mayúsculas y guiones.** `B-04` no encontraba nada pese a
  estar el alias, porque la comparación era por igualdad literal.
* **Estado compartido entre usuarios.** Los datos se recargaban por sesión; ahora
  se cargan una vez por proceso y el estado por usuario queda aislado.

### Seguridad

* Escapado de todo contenido de datos que llega al HTML del mapa.
* `enableXsrfProtection` activo y `showErrorDetails` desactivado en la
  configuración de Streamlit.
* El identificador de sesión de las métricas es aleatorio por visita y no permite
  reidentificar personas ni enlazar visitas (ver `docs/PRIVACIDAD.md`).

### Pendiente (documentado, no implementado)

Integración con U-Campus, mapa 3D con ruteo interior, geolocalización del usuario
y persistencia entre sesiones. Ver [docs/ROADMAP.md](docs/ROADMAP.md).

---

## [0.1.0] — prototipo original

Aplicación Streamlit de un archivo (`app.py`) con mapa folium sobre el plano,
búsqueda exacta por id o alias, trazado de ruta desde el acceso 850 u 851, y un
marcador de posición para el chat. Base de conocimiento en un documento maestro
usado como contexto del modelo.
