# Operación

Este proyecto tiene una característica incómoda: **su calidad se degrada sola**.
Los precios cambian, los plazos vencen, la gente cambia de oficina. Un asistente
que entrega con seguridad un dato vencido hace más daño que uno que dice no saber.
Por eso la actualización de contenidos es un requisito de funcionamiento, no una
mejora opcional.

## 1. Responsable de contenidos

Debe haber **una persona con nombre** responsable de la base de conocimiento, y
un reemplazo definido cuando esa persona se titule o deje el proyecto.

| Rol | Persona | Reemplazo |
|---|---|---|
| Contenidos (`data/kb/`) | _por definir_ | |
| Datos del campus (`data/*.json`) | _por definir_ | |
| Infraestructura y despliegue | _por definir_ | |

> Completar antes de la puesta en producción. Un proyecto de facultad sin esta
> tabla llena queda sin mantenedor en cuanto termina el semestre.

## 2. Calendario de revisión

| Cuándo | Qué revisar |
|---|---|
| Inicio de cada semestre | Cursos, horarios, salas, docentes. Es cuando más cambia todo |
| Mensual | Consultas sin respuesta del registro; agregar el contenido que falta |
| Mensual | `make validar`: contenidos vencidos y conflictos de alias |
| Semestral | Cuerpo funcionario: cargos, correos, teléfonos, ubicaciones |
| Ante aviso | Cambios anunciados por la facultad (obras, mudanzas, nuevos servicios) |

## 3. Revisar qué está quedando sin responder

El registro está en `var/logs/consultas.jsonl`, una línea JSON por consulta.

```bash
# Las 20 consultas al chat que quedaron sin respuesta, más frecuentes primero
grep '"estado": "sin_respuesta"' var/logs/consultas.jsonl \
  | python3 -c "import sys,json,collections; \
    c=collections.Counter(json.loads(l)['consulta'].lower() for l in sys.stdin); \
    [print(f'{n:4}  {q}') for q,n in c.most_common(20)]"

# Búsquedas en el mapa que no encontraron nada: lugares que faltan indexar
grep '"estado": "vacio"' var/logs/consultas.jsonl \
  | python3 -c "import sys,json,collections; \
    c=collections.Counter(json.loads(l)['consulta'].lower() for l in sys.stdin); \
    [print(f'{n:4}  {q}') for q,n in c.most_common(20)]"
```

Ese listado es la cola de trabajo de contenidos, ordenada por demanda real. Es
más útil que cualquier lluvia de ideas sobre qué agregar.

## 4. Incidentes

### La aplicación no arranca

Casi siempre son los datos. El mensaje de error nombra el registro y el campo.

```bash
make validar          # dice exactamente qué está mal
```

### El chat no responde o responde con error

1. Revisar los logs: `docker logs ubicate | grep -i "fallo del proveedor"`.
2. Verificar la API key y el saldo del proveedor.
3. Mitigación inmediata: `UBICATE_PROVEEDOR_LLM=eco` y reiniciar. La aplicación
   queda operativa con respuestas de la base mientras se resuelve el fondo.

### El chat inventó un dato

Es el incidente más grave del proyecto, porque erosiona lo único que sostiene la
herramienta: que se le pueda creer.

1. Reproducir la consulta y guardar la respuesta.
2. Revisar en "de dónde saqué esto" qué fragmentos se recuperaron.
3. Si el dato **no estaba** en la base: es un fallo de fundamentación. Reforzar
   la regla en `chat/prompts.py`, subir `VERSION_PROMPT` y agregar el caso a las
   pruebas.
4. Si el dato **estaba mal** en la base: corregir el contenido y su fecha.
5. Nota de actualización en ambos casos.

### El mapa aparece en blanco

Verificar que `assets/mapa_beauchef.png` esté dentro de la imagen desplegada
(`docker exec ubicate ls -la assets/`). Desde la v1.0.0 el plano se incrusta en
base64, así que si el archivo está, se ve.

## 5. Respaldos

| Qué | Dónde | Cómo |
|---|---|---|
| Datos y contenidos | Git | El repositorio es el respaldo |
| Registro de consultas | `var/logs/` | Copiar el volumen periódicamente |
| Configuración | Gestor de secretos | Según la política de la facultad |

## 6. Qué mirar de forma habitual

* Consultas por día y por origen (chat / buscador).
* Proporción de consultas sin respuesta — si sube, la base se quedó corta.
* Latencia del chat (`ms` en el registro).
* Errores del proveedor.
* Contenidos con vigencia vencida.
