# ADR-0007 · El chat ofrece los lugares como botones, no salta al mapa

- **Estado:** aceptada
- **Fecha:** 2026-09-08
- **Supera a:** [ADR-0002](ADR-0002-marca-de-lugar-para-el-mapa.md) (mantiene el
  contrato `[[LUGAR:ID]]`; cambia cuántas marcas y qué hace la aplicación con
  ellas). También revierte el salto automático chat → mapa que introdujo
  [ACT-004](../actualizaciones/ACT-004-interfaz-para-telefono.md).

## Contexto

Con ADR-0002 el modelo terminaba la respuesta con **una** marca `[[LUGAR:ID]]`,
"la del lugar más relevante", y la aplicación fijaba ese destino en el mapa.
Desde ACT-004, además, cambiaba sola a la vista del mapa.

Dos problemas en el uso real:

1. **Una consulta sugiere a menudo más de un lugar.** "¿Dónde rindo la prueba?"
   puede ser la B04 o la B12 según la sección; "¿dónde hay salas de estudio?"
   son varias. Obligar a elegir una sola descarta información que el estudiante
   necesita.
2. **El salto automático interrumpe.** El estudiante estaba leyendo la respuesta
   y la pantalla se le va al mapa sin pedirlo. Peor si el lugar al que salta no
   es el que le interesaba de los varios posibles.

## Decisión

- El prompt pide **una línea `[[LUGAR:ID]]` por cada lugar mencionado** que esté
  en el catálogo, en orden de relevancia, sin repetir, máximo cinco. Sube
  `VERSION_PROMPT` a 1.1.0.
- `Respuesta.destino` (uno) pasa a `Respuesta.destinos` (tupla). El motor reúne
  todas las marcas válidas más la coincidencia directa del buscador, sin
  duplicar. `Respuesta.destino` queda como propiedad que devuelve el primero,
  para las métricas.
- Bajo la respuesta del chat aparece **un botón por lugar** ("📍 Sala B04"). El
  mapa se abre —y la vista cambia— solo al pulsar un botón.
- Los botones se muestran solo bajo la **última** respuesta del asistente. El
  historial guarda los lugares y las citas de cada mensaje (`Mensaje.lugares`,
  `Mensaje.citas`) para poder redibujarlos al recargar.
- Se quita el efecto de `estado.fijar_destino` que cambiaba la vista a "mapa";
  ahora ese cambio es explícito en el botón.

## Alternativas consideradas

1. **Botones en todas las respuestas del historial, no solo la última.** Más
   completo, pero llena la conversación de botones viejos y obliga a arrastrar
   más estado. Si se pide, el dato ya está guardado en cada `Mensaje`.
2. **Mantener el salto automático cuando hay un solo lugar.** El comportamiento
   dependería del número de resultados. Se prefiere uno solo y predecible: el
   mapa nunca se abre sin que el usuario lo pida.
3. **Tool use / llamada a función** para devolver los lugares. Lo mismo que en
   ADR-0002: ata el diseño al proveedor y complica el modo eco. La marca de
   texto sigue funcionando con cualquiera.

## Consecuencias

**A favor**

- Una consulta con varios lugares los ofrece todos.
- El estudiante controla cuándo cambia de vista.
- Probar sigue siendo trivial: texto con varias marcas a un proveedor falso y se
  verifica la lista de destinos (`tests/test_motor.py`).

**En contra**

- Un paso más para ver el lugar en el mapa (un toque). Es el precio de no
  interrumpir y de soportar varios resultados.
- `Mensaje` carga dos campos de metadatos que los proveedores ignoran. A cambio,
  el historial se redibuja completo (citas incluidas) tras recargar.
- Depende de que el modelo escriba una marca por lugar. Igual que en ADR-0002:
  una marca inválida se ignora y queda el respaldo del buscador.

## Revisión

Igual que ADR-0002: al integrar U-Campus conviene revisar si la consulta
académica devuelve los lugares desde la base estructurada en vez de por marca.
