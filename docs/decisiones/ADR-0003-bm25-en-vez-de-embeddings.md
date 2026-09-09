# ADR-0003 · Recuperación BM25 en Python puro, sin embeddings

- **Estado:** aceptada
- **Fecha:** 2026-09-08

## Contexto

El prototipo pegaba el documento maestro completo en el prompt. Eso hace que el
costo por consulta crezca con el tamaño de la base, impide citar la fuente de
cada respuesta y no escala cuando se integre U-Campus.

Hay que recuperar solo los fragmentos pertinentes. La opción por defecto hoy son
embeddings con una base vectorial.

## Decisión

BM25 implementado a mano en `chat/conocimiento.py`, sin dependencias.

Razones:

- La base son ~67.000 caracteres en 299 fragmentos. BM25 los recorre en
  milisegundos.
- Las consultas reales son léxicas: "sala B04", "elimina especial", "paletas de
  ping pong", "SEMDA". Coinciden por palabra, que es exactamente donde BM25 es
  fuerte y donde los embeddings aportan poco.
- Sin costo por consulta, sin servicio adicional que mantener, sin modelo que
  descargar. Con presupuesto de proyecto universitario, cada servicio externo es
  un punto de falla y una cuenta que alguien tiene que seguir pagando.
- Es depurable a mano: se puede leer por qué salió un fragmento.

## Consecuencias

**A favor**

- Cero dependencias nuevas; el despliegue sigue siendo un contenedor.
- La recuperación funciona igual en modo eco, sin API key.

**En contra**

- No captura sinónimos que no comparten palabras: "dónde como" no recupera bien
  "espacios para almorzar". Se mitiga escribiendo los títulos de los fragmentos
  con las palabras que la gente usa, y se detecta con el registro de consultas
  sin respuesta.
- Sin manejo de plurales ni de raíces. Aceptable en esta escala.

## Revisión

Reevaluar si: la base supera unos 5.000 fragmentos, o el registro muestra un
patrón sostenido de consultas fallidas por vocabulario distinto. En ese caso la
capa a cambiar es solo `BaseConocimiento.buscar`; el resto del sistema no se
entera.
