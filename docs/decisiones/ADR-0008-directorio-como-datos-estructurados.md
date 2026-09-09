# ADR-0008 · El directorio de personas y unidades como datos estructurados

- **Estado:** propuesta (pendiente de revisión del equipo)
- **Fecha:** 2026-09-08
- **Relacionado:** ADR-0003 (BM25 para el texto narrativo — sigue vigente),
  `docs/ROADMAP.md` §1 (U-Campus)

## Contexto

La base de conocimiento (`data/kb/`) son tres archivos Markdown que se trocean
por párrafo y se recuperan con BM25 (ADR-0003). Funciona bien para texto
narrativo. Pero `02_cuerpo_funcionario.md` (42 KB, el 60 % de la base) **no es
texto narrativo**: es un directorio. Cada entrada tiene la misma forma —unidad,
descripción, integrantes (nombre + cargo), y un bloque de contacto (teléfono,
dirección, correo)— escrita como prosa.

Meterlo como párrafos tiene costos concretos:

- **La recuperación parte el registro.** El nombre de la unidad y su bloque de
  "Contacto" caen en fragmentos distintos. Una pregunta por el correo de una
  oficina puede traer el fragmento del nombre sin el correo, o al revés.
- **No escala.** Al agregar más personas, hay más párrafos casi idénticos
  compitiendo por las mismas palabras; BM25 pierde precisión para todos.
- **No se valida.** `make validar` no puede comprobar que cada persona tenga un
  correo bien formado o que cada unidad tenga contacto.
- **El prompt recibe ruido.** Llegan párrafos enteros cuando bastaría con los
  campos de la persona o unidad preguntada.

El equipo preguntó si convendría "una base de datos distinta". La respuesta
corta: sí conviene separar, pero **por la forma del dato, no agregando un motor
de base de datos**.

## Decisión propuesta

1. **Nuevo archivo `data/directorio.json`** con unidades y personas como datos
   estructurados, al mismo nivel que `edificios.json` y `salas.json`.
2. **Modelos en `modelos.py`** (`Unidad`, `Persona`) que validan el archivo al
   arrancar. La aplicación falla en el arranque, no frente al usuario.
3. **Repositorio e índice propios** (`datos/directorio.py`), con búsqueda por
   nombre de persona, por unidad y por cargo. Mismo patrón que
   `RepositorioCampus`: se carga una vez por proceso, sin estado por usuario.
4. **Rama nueva en `chat/motor.py`**: si la consulta es de tipo "quién / contacto
   / correo / teléfono / oficina de…", se resuelve contra el directorio y esos
   campos entran al prompt como datos limpios; el resto sigue por BM25. Es el
   enrutamiento híbrido que el ROADMAP §1 ya describe para U-Campus, en chico.
5. **`02_cuerpo_funcionario.md` se retira de `data/kb/`** una vez migrado su
   contenido. La migración es trabajo de transcripción cuidadosa: el dato ya
   está en el Markdown actual, **no se inventa nada** (regla 3.1).

### Por qué NO una base de datos (SQLite, Postgres)

- Todo el conjunto son kilobytes: cabe en memoria, se carga una vez.
- JSON + pydantic no agrega servicios, ni cuentas que pagar, ni puntos de falla
  — la misma razón por la que ADR-0003 rechazó la base vectorial.
- El equipo lo edita en un editor de texto y queda con historial en git.

SQLite empieza a valer la pena cuando haya que **cruzar varias tablas entre sí**
(cursos × bloques × salas × docentes — el caso U-Campus del ROADMAP §1) o cuando
los datos no quepan en memoria. Un directorio de contactos no es ninguna de las
dos. Cuando llegue U-Campus, esa integración traerá su propio ADR y ahí SQLite
es la opción correcta.

## Alcance y lo que queda fuera

- **Dentro:** unidades y personas de `02_cuerpo_funcionario.md` (dato público de
  directorios institucionales, ya recopilado).
- **Fuera:** cursos, horarios y "dónde está el profesor X en tal bloque". Eso es
  U-Campus (ROADMAP §1): necesita autorización institucional y una integración
  aparte. Los 6 cursos cargados a mano en `01_vida_en_campus.md` se quedan como
  están hasta ese momento.
- **Sensibilidad:** la localización de docentes se sigue presentando como
  horario académico publicado, nunca como ubicación en tiempo real (regla 8 de
  `CLAUDE.md`, `docs/PRIVACIDAD.md`). El directorio solo guarda contacto formal.

## Modelo de datos propuesto

```
Unidad
  id            identificador estable (p. ej. "arquitectura")
  nombre        "Oficina de Arquitectura"
  descripcion   qué hace (texto corto)
  depende_de    id de otra unidad, opcional
  telefonos     lista
  correo        opcional, validado
  direccion     texto (edificio y piso), opcional
  lugar_id      id del catálogo mapeable, opcional → enlaza con el mapa

Persona
  nombre        "Diego Peñailillo"
  cargo         "Jefe de la unidad"
  unidad_id     id de Unidad
  correo        opcional, validado
  telefono      opcional
```

`lugar_id` es el enganche con el mapa: si la unidad está en un edificio del
plano, el chat puede ofrecer también su botón "📍".

## Plan de implementación (por partes, revisable)

1. **Modelos + validación** (`modelos.py`, `scripts/validar_datos.py`): definir
   `Unidad` y `Persona`, cargar `data/directorio.json` (al principio con 2–3
   unidades de ejemplo reales), validar formato de correos y referencias.
2. **Repositorio e índice** (`datos/directorio.py`) + pruebas: búsqueda por
   nombre, unidad y cargo; normalización compartida con `busqueda/`.
3. **Migración del contenido**: transcribir `02_cuerpo_funcionario.md` a
   `directorio.json`, unidad por unidad, contrastando con el Markdown. Sin
   inventar; lo que no esté claro va a `docs/DEUDA_DATOS.md`.
4. **Rama en el motor** (`chat/motor.py`, `chat/prompts.py`): detección simple de
   intención "contacto/quién", consulta al directorio, formato de los campos en
   el prompt. Sube `VERSION_PROMPT`.
5. **Retirar** `02_cuerpo_funcionario.md` de `data/kb/` y actualizar
   `docs/DATOS.md`.
6. ADR a estado "aceptada", nota de actualización y CHANGELOG (versión **MAYOR**:
   cambia el esquema de `data/`).

Cada paso es un cambio acotado con sus pruebas; se puede parar entre uno y otro.

## Consecuencias

**A favor**

- Preguntas de contacto con respuesta exacta y sin ruido.
- `make validar` cubre el directorio.
- Agregar 100 personas no degrada la búsqueda del texto narrativo.
- Deja el molde para U-Campus: enrutamiento híbrido y enlace lugar → mapa.

**En contra**

- Es un cambio MAYOR: esquema nuevo y migración manual con cuidado.
- Una rama de intención más en el motor. Se mantiene simple (palabras clave), no
  un clasificador.
- Dos formas de guardar conocimiento (JSON estructurado y Markdown narrativo).
  Es justamente la distinción que se quiere: cada dato en la forma que le toca.
