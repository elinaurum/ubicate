# Plan de extensión

Recoge lo que la documentación del proyecto dejó diseñado y no implementado, más
lo que apareció durante la reestructuración. El orden refleja relación entre
esfuerzo y beneficio para el estudiante, no atractivo técnico.

## Prioridad alta

### 1. Integración con U-Campus

Resuelve la limitación L1 (cobertura de 6 cursos cargados a mano) y la deuda
D-05. Es lo que más cambiaría la utilidad real de la herramienta.

**Antes que nada: autorización institucional.** Nada de esto se implementa en
producción sin permiso formal de la facultad.

Arquitectura, ya diseñada en la documentación original:

```
U-Campus ──sincronización programada──► Ingesta (ETL)
                                             │
                                        Base relacional
                                   Cursos · Bloques · Salas · Docentes
                                             │
        consulta ──► clasificador de intención (LLM)
                          ├─ académica ──► consulta a la base (determinista)
                          └─ general ────► recuperación BM25 documental
                                             │
                                        redacción final por el LLM
```

Modelo de datos mínimo:

| Entidad | Campos |
|---|---|
| Curso | código, sección, nombre, departamento, semestre |
| Docente | id, nombre, correo, teléfonos, oficina, unidad |
| Sala | código, edificio, torre, piso, referencia al índice espacial |
| Bloque | curso_sección, tipo (cátedra/auxiliar/lab), día, hora inicio, hora fin, sala |
| Dicta | docente ↔ curso_sección (muchos a muchos) |

La decisión clave: **los horarios no entran al prompt como texto**. Son volátiles,
voluminosos y exigen precisión. Van a una base consultada por función, y el
modelo solo redacta. Elimina las alucinaciones de horario y permite actualizar
sin tocar prompts.

Casos de uso habilitados: en qué sala y horario se dicta un curso; qué cursos
dicta un docente; dónde está un docente en un bloque; qué hay ahora en una sala;
qué actividades hay hoy.

Enganche en este código: `chat/motor.py`, como rama previa a armar el contexto.
El campo `acceso` y el catálogo de lugares mapeables ya permiten enlazar la sala
resultante con el marcador.

**Restricción no negociable:** la localización de docentes se presenta siempre
como horario académico publicado, nunca como ubicación en tiempo real. Ver
`PRIVACIDAD.md`.

### 2. Ampliar el índice espacial

Deuda D-03, limitación M4. Esfuerzo bajo, beneficio inmediato: la base ya
menciona lugares que el mapa no sabe ubicar.

Priorizar con las búsquedas fallidas del registro (`OPERACION.md` §3).

### 3. Régimen de actualización con responsable

Limitación L2. No es código: es completar la tabla de responsables de
`OPERACION.md` y sostener el calendario de revisión. Sin esto, la herramienta se
degrada sola en un semestre.

## Prioridad media

### 4. Origen de ruta por geolocalización

El respaldo manual ya está implementado ("¿dónde estás ahora?"), que entrega la
mayor parte del beneficio sin infraestructura.

El paso siguiente es GPS en exteriores. El desafío específico del campus: buena
parte está bajo tierra —seis pisos subterráneos en 851— y ahí el GPS no sirve.

| Entorno | Tecnología | Precisión esperable |
|---|---|---|
| Exteriores | GPS del dispositivo | 5–10 m |
| Interiores y subterráneos | Huella WiFi o balizas BLE | 3–10 m |
| Respaldo universal | Selección manual (ya implementado) | exacta si acierta |

`repositorio.ruta(destino, origen_id)` ya acepta cualquier origen.

### 5. Aplicación móvil

Es el contexto natural de uso: uno pregunta dónde queda algo mientras camina, no
sentado frente a un computador. Primer paso barato: PWA con manifiesto e íconos
sobre la aplicación actual.

### 6. Perfil y persistencia entre sesiones

Limitación L3. Recordar carrera y año permitiría adaptar recomendaciones. Exige
resolver antes autenticación y política de datos personales; no es un cambio
técnico menor.

## Prioridad baja

### 7. Mapa 3D con ruteo interior

Limitación M1. Es la extensión más ambiciosa y la más costosa. Los planos
arquitectónicos ya se consiguieron.

1. Georreferenciar cada planta a un sistema común para apilar los pisos.
2. Construir el grafo de navegación: nodos en puertas, cruces, escaleras y
   ascensores; aristas con costo por distancia y penalización de escaleras.
3. Motor de ruteo (Dijkstra o A*), con variante accesible que evite escaleras.
4. Render por capas, con la ruta resaltada y posibilidad de aislar un piso.

**La ruta accesible no es un extra.** En un edificio de trece niveles es una
necesidad de primera línea para parte de la comunidad, y debe estar desde la
primera versión del ruteo, no agregarse después.

`Ruta` ya guarda una tupla de puntos, así que un camino con vértices intermedios
no obliga a cambiar el modelo ni el renderizador.

### 8. Reglas dedicadas para consultas sensibles

Hoy hay una instrucción general para bienestar y salud mental. Corresponde
desarrollarla con la unidad de la facultad que corresponda, en vez de que la
escriba el equipo de desarrollo por su cuenta.
