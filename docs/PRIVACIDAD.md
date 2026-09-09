# Privacidad

El proyecto atiende a estudiantes de su propia facultad. La confianza es el
activo, y se pierde una sola vez.

## Qué se registra

Cada consulta genera una línea en `var/logs/consultas.jsonl`:

```json
{"ts": "2026-09-08T14:22:01+00:00", "sesion": "a3f9c1d2e5b70418",
 "origen": "chat", "consulta": "donde almuerzo", "estado": "respondido",
 "destino_id": "850_CASINO", "ms": 1840, "proveedor": "anthropic"}
```

## Qué NO se registra

* Nombre, correo, RUT, matrícula ni ningún identificador de la persona.
* Dirección IP.
* Sesión de U-Campus o cualquier credencial.
* El texto de las respuestas del asistente.
* Ubicación física del usuario.

## Sobre el identificador de sesión

`sesion` es un valor **aleatorio generado en cada visita**. No deriva de ningún
dato de la persona y no se guarda en el navegador: al recargar la página se
genera otro. Sirve para saber cuántas consultas tuvo una misma visita —útil para
entender si la gente reformula porque no encuentra— y no permite reidentificar a
nadie ni enlazar dos visitas distintas.

## Sobre el texto de las consultas

Se guarda porque es lo único que permite saber qué está quedando sin responder.
Tiene un riesgo: alguien puede escribir algo personal en el chat.

Medidas:

* La consulta se trunca a 200 caracteres.
* No se enlaza con ninguna identidad.
* El registro se puede desactivar por completo con `UBICATE_METRICAS_ACTIVAS=false`.
* **Purgar el registro cada seis meses.** Para priorizar contenidos basta la
  historia reciente; conservar años de consultas no aporta y sí agrega riesgo.

Antes de un despliegue institucional, revisar esta política con la unidad que
corresponda en la facultad.

## Datos de personas en la base de conocimiento

`data/kb/` contiene nombres, cargos, correos y teléfonos de funcionarios y
docentes. Todos provienen de **directorios institucionales públicos**. La regla
es estricta: solo entra a la base lo que ya es público en un canal oficial de la
FCFM. Si alguien pide que se retire su dato, se retira.

## Localización de docentes

El asistente puede decir en qué sala está dictando clases un docente en un
bloque dado. Está encuadrado, por instrucción explícita en el prompt, como
**consulta de horario académico publicado**, nunca como ubicación de una persona
en tiempo real, y siempre priorizando los canales formales de contacto. La
distinción no es cosmética: lo primero es información pública de la facultad, lo
segundo sería seguimiento de personas.

Esta regla debe mantenerse si se implementa la integración con U-Campus.

## Geolocalización (cuando se implemente)

Compromisos de diseño, para no negociarlos después bajo presión de plazo:

* Consentimiento explícito, pedido en el momento y no enterrado en un aviso.
* Procesamiento en el dispositivo.
* Sin almacenamiento ni asociación a perfil.
* La aplicación sigue siendo plenamente usable si la persona lo rechaza.
