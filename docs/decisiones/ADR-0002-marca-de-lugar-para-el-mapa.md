# ADR-0002 · Contrato `[[LUGAR:ID]]` entre el modelo y la aplicación

- **Estado:** superada por [ADR-0007](ADR-0007-varios-lugares-con-botones.md)
- **Fecha:** 2026-09-08

> El contrato `[[LUGAR:ID]]` sigue vigente. Lo que cambió en ADR-0007: el modelo
> escribe una marca por cada lugar (no una sola) y la aplicación las ofrece como
> botones en el chat en vez de fijar el destino y saltar al mapa.

## Contexto

El Objetivo 3 del proyecto era integrar chat y mapa. El prototipo logró la
integración de interfaz —conviven en la misma pantalla— pero no la funcional: el
chatbot decía "la sala B06 está en el piso −1" y el usuario tenía que copiar
"B06" al buscador. La documentación identificó la causa: el modelo devuelve texto,
no un dato que la aplicación pueda consumir.

## Alternativas consideradas

1. **Detectar nombres de lugares en el texto de la respuesta.** Frágil: el modelo
   puede mencionar tres lugares y no hay forma de saber cuál es el destino;
   además obliga a mantener un detector aparte del índice.
2. **Llamada a función (tool use).** Es la solución correcta a mediano plazo,
   pero ata el diseño a las capacidades de cada proveedor y complica el modo eco.
3. **Marca en la respuesta.** El modelo termina con `[[LUGAR:ID]]`; la aplicación
   la extrae, la valida contra el índice y la borra del texto que se muestra.

## Decisión

La 3. El prompt entrega el catálogo de identificadores válidos y pide una marca
al final. El motor la valida contra el repositorio: si el identificador no
existe, se ignora sin romper nada, y queda el respaldo de la coincidencia directa
del buscador.

## Consecuencias

**A favor**

- Funciona con cualquier proveedor, incluidos los que no tienen tool use.
- La validación contra el índice evita que un identificador alucinado llegue al
  mapa.
- Trivial de probar: se le pasa un texto con marca a un proveedor falso y se
  verifica el destino resultante.

**En contra**

- Depende de que el modelo respete el formato. Mitigado porque hay respaldo y
  porque la marca inválida no rompe nada.
- El catálogo ocupa lugar en el prompt (~60 entradas hoy). Si crece mucho habrá
  que filtrarlo por pertinencia antes de armar el contexto.

## Revisión

Reevaluar cuando se integre U-Campus: ahí sí conviene tool use, porque la
consulta académica necesita un resultado determinista de una base y no un texto.
